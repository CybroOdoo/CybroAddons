# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64
import json
import logging
import os
import re
import time

from urllib.parse import urlparse

import requests
from markupsafe import Markup

from odoo import fields, http
from odoo.exceptions import AccessError, UserError
from odoo.http import request

from odoo.addons.mail.tools.discuss import add_guest_to_context

from ..models.res_config_settings import DEBUG_AUDIO_DIR
from ..tools import cloud_whisper, grok_stt, stt_client

_logger = logging.getLogger(__name__)

DEBUG_AUDIO_KEEP = 50
CLOUD_STT_TIMEOUT = 15  # a final caption later than this is stale anyway
CLOUD_ENGINES = ('grok', 'cloud_whisper')  # no local model: billed per request
LANGUAGE_CODE = re.compile(r"^[a-z]{2,3}$")
MAX_SPEECH_WORKERS = 4


def _save_debug_audio(audio_bytes, channel_id):
    """Keep the last few received utterances on disk so they can be listened to."""
    try:
        os.makedirs(DEBUG_AUDIO_DIR, exist_ok=True)
        path = os.path.join(DEBUG_AUDIO_DIR, "%d_ch%s.wav" % (int(time.time() * 1000), channel_id))
        with open(path, "wb") as f:
            f.write(audio_bytes)
        for old in sorted(os.listdir(DEBUG_AUDIO_DIR))[:-DEBUG_AUDIO_KEEP]:
            os.unlink(os.path.join(DEBUG_AUDIO_DIR, old))
        return path
    except OSError:
        _logger.exception("Could not save debug audio")
        return None


def _self_call_member(channel_id):
    """The requester's own member of ``channel_id`` (user or guest), if they are in its call."""
    try:
        channel_id = int(channel_id)
    except (TypeError, ValueError):
        return request.env["discuss.channel.member"]
    member = request.env["discuss.channel.member"].search([
        ("channel_id", "=", channel_id),
        ("is_self", "=", True),
    ], limit=1)
    return member if member.sudo().rtc_session_ids else member.browse()


def _cloud_error_message(exc, provider):
    """Why a cloud engine's caption was lost, for the speaker to read.

    ``exc`` is a GrokSttError or CloudWhisperError (same ``kind`` and ``status``); ``provider``
    names who answered: 'xAI', or the host of the Cloud Whisper URL.
    """
    if exc.kind == 'rate_limit':
        return request.env._("Captions skipped: %s has reached this account's request limit. "
                             "They resume when the limit resets; a paid plan raises it.", provider)
    if exc.kind == 'auth':
        return request.env._("Captions failed: %s rejected the API key. Check it under Settings > Discuss > "
                             "Meeting Subtitles & AI Summaries.", provider)
    if exc.kind == 'timeout':
        return request.env._("Caption skipped: %(provider)s did not answer within %(seconds)s seconds.",
                             provider=provider, seconds=CLOUD_STT_TIMEOUT)
    if exc.kind == 'unreachable':
        return request.env._("Captions failed: %s could not be reached. Check this server's internet connection.",
                             provider)
    if exc.status:
        return request.env._("Caption failed: %(provider)s returned an error (HTTP %(status)s).",
                             provider=provider, status=exc.status)
    return request.env._("Caption failed: %s could not transcribe it.", provider)


def _engine_not_installed_message(engine):
    """Why a local engine's caption was lost: its Python package is not on the server."""
    return request.env._("Captions failed: the %(engine)s speech engine is not installed on this server. "
                         "An administrator can install it with: pip install %(package)s",
                         engine=engine.capitalize(), package=stt_client.ENGINE_PACKAGES[engine])


def _speech_workers(get_param):
    """How many captions the speech worker may transcribe at once (the Speech Workers setting).

    More than one only helps on a CPU with cores to spare: otherwise the captions share them,
    and each takes as much longer.
    """
    try:
        workers = int(get_param('meeting_transcription_summary.stt_workers', 1))
    except (TypeError, ValueError):
        return 1
    return min(max(workers, 1), MAX_SPEECH_WORKERS)


def _local_engine(engine):
    """The local engine ('whisper' or 'whistle') that transcribes captions, or None for a cloud engine."""
    if engine in CLOUD_ENGINES:
        return None
    return 'whistle' if engine == 'whistle' else 'whisper'


def _warm_up_speech_engine(ai_state):
    """Load the local speech model as soon as the call needs captions, not on the first caption."""
    if not ai_state.get('subtitles') and not ai_state.get('transcribe'):
        return
    get_param = request.env['ir.config_parameter'].sudo().get_param
    engine = get_param('meeting_transcription_summary.stt_engine', 'whisper')
    model = get_param('meeting_transcription_summary.whisper_model', 'small')
    workers = _speech_workers(get_param)
    local_engine = _local_engine(engine)
    if local_engine:
        stt_client.warm_up(local_engine, model, workers)


class DiscussMeetingAiController(http.Controller):

    @http.route("/discuss/meeting/transcribe_chunk", type="http", auth="public", methods=["POST"])
    @add_guest_to_context
    def transcribe_chunk(self, **kwargs):
        """Server-side audio transcription endpoint that enables 100% browser independence.
        Works across all browsers (including Firefox, Chrome, Edge, Safari, Opera) by receiving
        raw audio chunks recorded via standard MediaRecorder.
        """
        request_started = time.monotonic()
        channel_id = kwargs.get('channel_id')
        audio_file = request.httprequest.files.get('file')

        if not audio_file or not channel_id:
            return request.make_response(
                json.dumps({"error": "Missing audio file or channel_id"}),
                headers=[("Content-Type", "application/json")],
            )

        # Only participants of the channel's call (users or guests) may transcribe into it.
        member = _self_call_member(channel_id)
        if not member:
            return request.make_response(
                json.dumps({"error": "Channel not found"}),
                status=403,
                headers=[("Content-Type", "application/json")],
            )
        channel = member.channel_id.sudo()
        # Never trust a client-supplied name: use the member's own persona.
        speaker_name = member.partner_id.name or member.guest_id.name or request.env._("Speaker")

        # Speech is only transcribed for a purpose: someone watches subtitles, or the call is
        # being transcribed. The browser stops sending once it learns neither is on.
        ai_state = channel._get_meeting_ai_state()
        if not ai_state['subtitles'] and not ai_state['transcribe']:
            return request.make_response(
                json.dumps({"status": "idle", "text": "", **ai_state}),
                headers=[("Content-Type", "application/json")],
            )

        audio_bytes = audio_file.read()
        if len(audio_bytes) < 1000:
            return request.make_response(
                json.dumps({"status": "empty_chunk"}),
                headers=[("Content-Type", "application/json")],
            )

        get_param = request.env['ir.config_parameter'].sudo().get_param
        api_key = get_param('meeting_transcription_summary.openai_api_key', '')
        language = get_param('meeting_transcription_summary.subtitles_language', 'en-US')
        whisper_model = get_param('meeting_transcription_summary.whisper_model', 'small')
        main_language = get_param('meeting_transcription_summary.main_language', 'en-US')
        workers = _speech_workers(get_param)

        engine = get_param('meeting_transcription_summary.stt_engine', 'whisper')
        # Hotwords: configured terms plus the names of the people currently in the call
        # (not every channel member: in a big channel that would mostly be absentees).
        keywords = [k.strip() for k in (get_param('meeting_transcription_summary.keywords', '') or '').replace('\n', ',').split(',') if k.strip()]
        in_call = channel.rtc_session_ids.channel_member_id
        names = in_call.mapped('partner_id.name') + in_call.mapped('guest_id.name')
        keywords += [n for n in names if n and n not in keywords]
        keywords = keywords[:30]

        # With auto-detection, the browser sends back the language it already detected for this
        # speaker: re-detecting on every short clip is unreliable and makes captions flip language.
        if language == 'auto' and LANGUAGE_CODE.match(kwargs.get('language') or ''):
            language = kwargs['language']
        if get_param('meeting_transcription_summary.save_debug_audio') in ('True', '1'):
            debug_path = _save_debug_audio(audio_bytes, channel.id)
            _logger.info("Subtitle debug audio saved: %s (%d bytes)", debug_path, len(audio_bytes))

        text = ""
        detected_language, language_probability = None, 0.0
        # timing log: where each caption's delay goes (waiting for the engine vs. transcribing)
        waited = transcribing = 0.0
        outcome, used_engine = "empty", engine
        # Whether a configured engine answered: no words from it is silence, not a reason to
        # send the audio to OpenAI. Only an engine failure (error, busy, not installed) is.
        engine_answered = False
        caption_error = None  # why a caption was lost (cloud error, engine not installed), shown to the speaker
        if engine == 'grok':
            # Cloud engine: no local model, no queue. The local engines are not tried after it, as their first use may load a model
            # for minutes; the OpenAI fallback below still is.
            xai_api_key = get_param('meeting_transcription_summary.xai_api_key', '')
            if xai_api_key:
                call_started = time.monotonic()
                try:
                    result = grok_stt.transcribe(
                        audio_bytes, xai_api_key, language=language, keywords=keywords,
                        timeout=CLOUD_STT_TIMEOUT)
                    text = (result.get('text') or '').strip()
                    engine_answered = True
                    # Grok reports no confidence: the browser locks the speaker's language only
                    # once two captions agree, then sends it back to bias recognition
                    detected_language = result.get('language')
                except grok_stt.GrokSttError as exc:
                    outcome = "failed"
                    caption_error = _cloud_error_message(exc, 'xAI')
                    _logger.warning("Grok STT failed: %s", exc)
                transcribing += time.monotonic() - call_started
            else:
                outcome = "failed"
                caption_error = request.env._("Captions failed: no xAI API key is set for Grok STT. Add it under "
                                              "Settings > Discuss > Meeting Subtitles & AI Summaries.")
                _logger.warning("Grok STT is the speech engine but no xAI API key is set")
        elif engine == 'cloud_whisper':
            # Whisper behind an OpenAI-compatible API (Groq, OpenAI, a GPU server of your own):
            # like Grok, the OpenAI fallback below is still tried after it
            call_started = time.monotonic()
            cloud_url = get_param('meeting_transcription_summary.cloud_whisper_url') or cloud_whisper.DEFAULT_URL
            try:
                result = cloud_whisper.transcribe(
                    audio_bytes,
                    get_param('meeting_transcription_summary.cloud_whisper_api_key', ''),
                    url=cloud_url,
                    model=get_param('meeting_transcription_summary.cloud_whisper_model') or cloud_whisper.DEFAULT_MODEL,
                    language=language, keywords=keywords, timeout=CLOUD_STT_TIMEOUT)
                text = result['text']
                engine_answered = True
                # no language confidence either: the browser locks the language once two captions agree
                detected_language = result['language']
            except cloud_whisper.CloudWhisperError as exc:
                outcome = "failed"
                caption_error = _cloud_error_message(exc, urlparse(cloud_url).hostname or cloud_url)
                _logger.warning("Cloud Whisper failed: %s", exc)
            transcribing += time.monotonic() - call_started
        # Local engines: 'whisper' (default) or 'whistle'
        local_engine = _local_engine(engine)
        if local_engine:
            used_engine = local_engine
            call_started = time.monotonic()
            try:
                # greedy decoding (beam 1): several times faster, which live captions need more
                # than the small accuracy gain of a wider beam
                # No previous caption as context: Whisper then skips speech it takes for already
                # transcribed, or invents text ("Thank you for watching.") in its place.
                result = stt_client.transcribe_with_info(
                    audio_bytes, local_engine, language, whisper_model, keywords, beam_size=1,
                    main_language=main_language, workers=workers)
                text = result['text']
                detected_language = result['language']
                language_probability = result['language_probability']
                engine_answered = True
                waited += result['queue_seconds']
                transcribing += result['stt_seconds']
            except stt_client.SttWorkerUnavailable as exc:
                outcome = "busy" if "busy" in str(exc) else "unavailable"
                waited += time.monotonic() - call_started
                if str(exc).startswith("not_installed"):
                    caption_error = _engine_not_installed_message(local_engine)
                _logger.info("Speech engine %s unavailable: %s", local_engine, exc)
            except stt_client.SttWorkerError:
                outcome = "failed"
                transcribing += time.monotonic() - call_started
                _logger.exception("Speech engine %s failed", local_engine)

        # Cloud fallback: OpenAI Whisper API, only when the speech engine failed and the admin
        # opted in (the key alone may be there for summaries only)
        openai_fallback = get_param('meeting_transcription_summary.stt_openai_fallback') in ('True', '1')
        if openai_fallback and api_key and not engine_answered:
            used_engine += "+openai"
            call_started = time.monotonic()
            try:
                files = {
                    'file': ('audio.wav' if audio_bytes[:4] == b'RIFF' else 'audio.webm', audio_bytes, 'audio/wav' if audio_bytes[:4] == b'RIFF' else 'audio/webm'),
                    'model': (None, 'whisper-1'),
                }
                if language and language != 'auto':
                    lang_code = language.split('-')[0]
                    files['language'] = (None, lang_code)

                response = requests.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files=files,
                    timeout=12,
                )
                if response.status_code == 200:
                    text = response.json().get('text', '').strip()
                else:
                    _logger.warning("Whisper transcription API returned: %s", response.text)
            except Exception as e:
                _logger.warning("Failed server-side Whisper transcription: %s", e)
            transcribing += time.monotonic() - call_started

        if text and ai_state['subtitles']:
            partner = request.env.user.partner_id
            channel._broadcast_meeting_subtitle(
                partner_name=speaker_name,
                text=text,
                partner_id=partner.id if partner else None,
                member_id=member.id,
            )
        # Each browser sends only its own microphone, so the speaker's own request records
        # the line once for the whole meeting (only while the call is being transcribed).
        if text and ai_state['transcribe']:
            request.env["discuss.meeting.summary"].sudo()._add_transcript_line(
                channel, member, speaker_name, text)

        if text:
            outcome = "ok"
        _logger.info(
            "caption ch=%s member=%s audio=%s %s engine=%s wait=%.2fs stt=%.2fs total=%.2fs chars=%d",
            channel.id, member.id,
            "%.1fs" % ((len(audio_bytes) - 44) / 32000) if audio_bytes[:4] == b'RIFF' else "?",  # 16 kHz PCM16 mono
            outcome, used_engine,
            waited, transcribing, time.monotonic() - request_started, len(text))

        return request.make_response(
            json.dumps({
                "status": "ok",
                "text": text,
                "language": detected_language,
                "language_probability": language_probability,
                # only for a caption that was lost (the OpenAI fallback may have saved it)
                **({"caption_error": caption_error} if caption_error and not text else {}),
                **ai_state,
            }),
            headers=[("Content-Type", "application/json")],
        )

    @http.route("/discuss/meeting/state", type="jsonrpc", auth="public", methods=["POST"])
    @add_guest_to_context
    def get_meeting_ai_state(self, channel_id):
        """Whether the call is being transcribed and whether anyone watches subtitles."""
        member = _self_call_member(channel_id)
        if not member:
            return {"error": "not_in_call"}
        ai_state = member.channel_id.sudo()._get_meeting_ai_state()
        _warm_up_speech_engine(ai_state)
        return ai_state

    @http.route("/discuss/meeting/set_transcribe", type="jsonrpc", auth="public", methods=["POST"])
    @add_guest_to_context
    def set_meeting_transcribe(self, channel_id, enabled):
        """Turns transcription into the meeting summary on or off for the whole call.

        Internal users only: it records everyone in the call into a meeting that only internal
        users can read, so guests and portal users may not start or stop it.
        """
        member = _self_call_member(channel_id)
        if not member:
            return {"error": "not_in_call"}
        if not request.env.user._is_internal():  # guests run as the public user
            return {"error": "not_allowed"}
        channel = member.channel_id.sudo()
        meeting = request.env["discuss.meeting.summary"].sudo()._get_live_meeting(channel, create=True)
        if not meeting:
            return {"error": "not_in_call"}  # no running call history: nothing to transcribe into
        meeting.transcribe_enabled = bool(enabled)
        channel._broadcast_meeting_ai_state()
        ai_state = channel._get_meeting_ai_state()
        _warm_up_speech_engine(ai_state)
        return ai_state

    @http.route("/discuss/meeting/set_subtitles", type="jsonrpc", auth="public", methods=["POST"])
    @add_guest_to_context
    def set_meeting_subtitles(self, channel_id, enabled):
        """Turns Subtitle(CC) on or off for the requester: while anyone watches, everyone is captioned."""
        member = _self_call_member(channel_id)
        if not member:
            return {"error": "not_in_call"}
        channel = member.channel_id.sudo()
        member.sudo().rtc_session_ids.meeting_subtitles_on = bool(enabled)
        channel._broadcast_meeting_ai_state()
        ai_state = channel._get_meeting_ai_state()
        _warm_up_speech_engine(ai_state)
        return ai_state

    @http.route("/discuss/meeting/transcript", type="jsonrpc", auth="user", methods=["POST"])
    def get_meeting_transcript(self, channel_id):
        """The running call's transcript so far, for the meeting assistant dialog."""
        member = _self_call_member(channel_id)
        if not member:
            return {"error": "not_in_call"}
        meeting = request.env["discuss.meeting.summary"].sudo()._get_live_meeting(member.channel_id)
        return {
            "transcribe": bool(meeting.transcribe_enabled),
            "lines": [{
                "id": line.id,
                "time": fields.Datetime.context_timestamp(line, line.time).strftime('%H:%M:%S'),
                "speaker": line.speaker_name,
                "text": line.text,
            } for line in meeting.transcript_line_ids],
        }

    @http.route("/discuss/meeting/summarize", type="jsonrpc", auth="user", methods=["POST"])
    def summarize_meeting(self, channel_id, **kwargs):
        """Summarizes the running call's meeting from everything transcribed so far.

        The meeting is shared by all participants, so summarizing again refreshes the same
        record instead of creating a new one.
        """
        channel = request.env["discuss.channel"].search([("id", "=", int(channel_id)), ("is_member", "=", True)])
        if not channel:
            return {"error": request.env._("Channel not found")}
        meeting = request.env["discuss.meeting.summary"].sudo()._get_live_meeting(channel)
        if not meeting or not meeting.transcript_line_ids:
            return {"error": request.env._("Nothing has been transcribed in this call yet. Turn on Transcribe to record the conversation.")}
        meeting = meeting.sudo(False)  # back to the user's rights: a member of the channel
        meeting.action_generate_summary()

        return {
            "status": "success",
            "summary_id": meeting.id,
            "title": meeting.name,
            "executive_summary": meeting.executive_summary,
            "key_discussion_points": meeting.key_discussion_points,
            "decisions": meeting.decisions,
            "action_items": meeting.action_items,
        }

    @http.route("/discuss/meeting/post_summary", type="jsonrpc", auth="user", methods=["POST"])
    def post_meeting_summary(self, summary_id):
        """Posts the AI summary to the channel."""
        summary = request.env["discuss.meeting.summary"].browse(int(summary_id))
        if not summary.exists():
            return {"error": request.env._("Summary not found")}
        if summary.state == 'posted':
            return {"error": request.env._("This summary has already been posted to the channel.")}

        summary.action_post_to_channel()
        return {"status": "posted"}

    @http.route("/discuss/meeting/generate_summary_redirect", type="http", auth="user", methods=["GET", "POST"])
    def generate_summary_redirect(self, summary_id, **kwargs):
        """Target of 'Generate AI Summary Now' on the call-ended chatter card.

        The link (GET) only shows a confirmation page: generating and posting happens on its
        POST, which Odoo checks for a CSRF token, so a link or image planted elsewhere cannot
        make a member post a summary.
        """
        try:
            summary = request.env["discuss.meeting.summary"].browse(int(summary_id)).exists()
        except (TypeError, ValueError):
            summary = request.env["discuss.meeting.summary"]
        if not summary:
            return request.redirect("/odoo/discuss")
        if request.httprequest.method == "POST":
            summary.action_generate_and_post_summary()
            return request.redirect(f"/odoo/discuss?channel_id={summary.channel_id.id}")
        if summary.state == 'posted':
            return request.redirect(f"/odoo/discuss?channel_id={summary.channel_id.id}")
        page = Markup("""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>%(title)s</title></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f8fafc; margin: 0; padding: 48px 16px;">
<form method="post" style="max-width: 480px; margin: 0 auto; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px;">
<input type="hidden" name="csrf_token" value="%(csrf)s"/>
<h2 style="margin: 0 0 8px; font-size: 18px; color: #111827;">%(title)s</h2>
<p style="margin: 0 0 20px; color: #475569; font-size: 14px;">%(question)s</p>
<button type="submit" style="background: #2563eb; color: #fff; border: 0; border-radius: 6px; padding: 8px 16px; font-size: 14px; cursor: pointer;">%(confirm)s</button>
<a href="/odoo/discuss?channel_id=%(channel_id)s" style="margin-left: 12px; color: #475569; font-size: 14px;">%(cancel)s</a>
</form></body></html>""") % {
            'title': summary.name,
            'csrf': request.csrf_token(),
            'question': request.env._("Generate the AI summary of this meeting and post it to %s?",
                                             summary.channel_id.display_name),
            'confirm': request.env._("Generate & Post Summary"),
            'cancel': request.env._("Cancel"),
            'channel_id': summary.channel_id.id,
        }
        return request.make_response(page, headers=[("Content-Type", "text/html; charset=utf-8")])

    @http.route("/discuss/meeting/upload_recording", type="http", auth="user", methods=["POST"])
    def upload_meeting_recording(self, **kwargs):
        """Video/audio recording uploaded from a Discuss channel.

        It is transcribed in the background; the summary is posted to the channel when it is ready.
        """
        channel_id = kwargs.get("channel_id")
        title = kwargs.get("title")
        duration_minutes = kwargs.get("duration_minutes") or 15
        recording_file = request.httprequest.files.get("file")

        if not channel_id or not recording_file:
            return request.make_response(
                json.dumps({"status": "error", "error": request.env._("Missing channel_id or file")}),
                headers=[("Content-Type", "application/json")],
            )

        channel = request.env["discuss.channel"].search([("id", "=", int(channel_id)), ("is_member", "=", True)])
        if not channel:
            return request.make_response(
                json.dumps({"status": "error", "error": request.env._("Channel not found")}),
                headers=[("Content-Type", "application/json")],
            )

        filename = recording_file.filename or "recording.mp4"
        file_bytes = recording_file.read()
        if not file_bytes:
            return request.make_response(
                json.dumps({"status": "error", "error": request.env._("Uploaded file is empty")}),
                headers=[("Content-Type", "application/json")],
            )

        channel_title = channel.name or channel.display_name or request.env._("Channel")
        meeting_title = title if (title and title.strip()) else request.env._("Recording: %s", channel_title)
        attendees = channel.channel_member_ids.mapped('partner_id')

        try:
            # a failed upload must leave nothing behind: no summary, no stored recording
            with request.env.cr.savepoint():
                summary = request.env["discuss.meeting.summary"].create({
                    'name': meeting_title,
                    'channel_id': channel.id,
                    'recording_file': base64.b64encode(file_bytes),
                    'recording_filename': filename,
                    'duration_minutes': int(duration_minutes or 15),
                    'attendee_ids': [(6, 0, attendees.ids)],
                })
                # transcribed in the background: a whole recording takes far longer than a request may run
                summary._queue_recording_transcription(post=True)

            return request.make_response(
                json.dumps({
                    "status": "success",
                    "summary_id": summary.id,
                    "title": summary.name,
                    "message": request.env._("Recording uploaded. It is being transcribed in the background: the summary "
                                 "will be posted to the channel when it is ready, and you will be notified."),
                }),
                headers=[("Content-Type", "application/json")],
            )
        except (UserError, AccessError) as e:
            # written for the user (not allowed, invalid file...)
            return request.make_response(
                json.dumps({"status": "error", "error": str(e)}),
                headers=[("Content-Type", "application/json")],
            )
        except Exception:
            # internal details stay in the log
            _logger.exception("Error processing meeting recording upload")
            return request.make_response(
                json.dumps({"status": "error", "error": request.env._("The recording could not be saved. Please try again.")}),
                headers=[("Content-Type", "application/json")],
            )
