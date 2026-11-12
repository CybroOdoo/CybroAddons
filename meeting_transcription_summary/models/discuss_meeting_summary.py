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
from datetime import timedelta

import requests
from babel.dates import format_date, format_interval
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config
from odoo.tools.misc import babel_locale_parse, get_lang

from ..tools import stt_client

_logger = logging.getLogger(__name__)

RECORDING_JOB_POLL = timedelta(seconds=20)  # how often running recording jobs are checked
RECORDING_JOB_MAX_DURATION = timedelta(hours=6)  # a job still running after this is stopped
MAX_RUNNING_JOBS = {'whisper': 1, 'grok': 4}

# Built-in summarizer: how it tells an action item from the rest of a spoken transcript.
_DAYS = r"monday|tuesday|wednesday|thursday|friday|saturday|sunday"
# Phrases that state a task whoever says them
ACTION_PHRASE_RE = re.compile(
    r"\b(?:needs? to|have to|has to|todo|to-do|action items?|follow(?:ing)?[ -]up|assign(?:ed)? to"
    r"|plan(?:ning)? to|deadline|next steps?|take care of|look into|responsible for|in charge of"
    r"|let me|by (?:" + _DAYS + r"|tomorrow|tonight|today|eod|eow|next week"
    r"|the end of (?:the )?(?:day|week|month)|end of (?:the )?(?:day|week|month)))\b",
    re.IGNORECASE)
# A promise: someone will do something ("I'll", "we will", "Priya is going to", "they're gonna")
COMMITMENT_RE = re.compile(
    r"\b([A-Za-z]+)(?:\s+(?:will|shall|must)|'ll|\s+(?:am|is|are)\s+going\s+to|'(?:m|s|re)\s+going\s+to"
    r"|(?:'(?:m|s|re))?\s+gonna)\s+\w",
    re.IGNORECASE)
PERSON_PRONOUNS = {'i', 'we', 'you', 'he', 'she', 'they'}
# Capitalized words that come before "will" but are no person: "It will rain", "Monday will be busy"
NOT_A_PERSON = {
    'it', 'this', 'that', 'there', 'here', 'what', 'which', 'who', 'everything', 'nothing', 'something',
    'anything', 'these', 'those', 'today', 'tomorrow', 'tonight', 'the', 'a', 'an', 'so', 'then', 'and',
    'but', 'or', 'if', 'when', 'maybe', 'also', 'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december', *_DAYS.split('|')}
# A request to someone: "Can you check it?", "Arun, could you send it?", "Please update the sheet."
REQUEST_RE = re.compile(r"^(?:([A-Za-z]+),\s*)?(?:please|(?:can|could|would|will) you)\b", re.IGNORECASE)
# Checking the call itself is no request: "Can you hear me?", "Could you see my screen?"
CALL_CHECK_RE = re.compile(r"\b(?:can|could|do) you (?:hear|see)\b", re.IGNORECASE)
REQUEST_ADDRESSEE_END_RE = re.compile(r",\s*([A-Z][a-z]+)\s*[?.!]*$")
# Words before or after the comma of a request that name no one: "Okay, can you…", "…, everyone?"
NOT_AN_ADDRESSEE = NOT_A_PERSON | PERSON_PRONOUNS | {
    'please', 'okay', 'ok', 'yes', 'yeah', 'no', 'well', 'hey', 'hi', 'hello', 'alright', 'right', 'now',
    'guys', 'everyone', 'everybody', 'team', 'all', 'folks', 'sir', 'madam', 'thanks'}
# "I will send it" / "We'll send it" / "I'm going to send it" / "Let me send it" -> "Will send it"
SELF_COMMITMENT_RE = re.compile(
    r"^(?:(?:i|we)(?:\s+will|'ll|\s+(?:am|are)\s+going\s+to|'(?:m|re)\s+going\s+to)|let me)\s+",
    re.IGNORECASE)


class DiscussMeetingSummary(models.Model):
    _name = 'discuss.meeting.summary'
    _description = 'Discuss Meeting Summary & Notes'
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Meeting Title',
        required=True,
        default=lambda self: self.env._('Meeting on %s', fields.Datetime.now().strftime('%Y-%m-%d %H:%M')),
    )
    channel_id = fields.Many2one(
        'discuss.channel',
        string='Discuss Channel',
        required=True,
        ondelete='cascade',
    )
    date = fields.Datetime(
        string='Meeting Date',
        default=fields.Datetime.now,
        required=True,
    )
    duration_minutes = fields.Integer(
        string='Duration (Minutes)',
        default=1,
    )
    attendee_ids = fields.Many2many(
        'res.partner',
        string='Attendees',
    )
    recording_file = fields.Binary(
        string='Meeting Video / Audio File',
        attachment=True,
        help='Upload a meeting recording (.mp4, .webm, .mkv, .mov, .mp3, .wav, .m4a) to automatically transcribe and summarize.',
    )
    recording_filename = fields.Char(string='Recording File Name')
    raw_transcript = fields.Text(
        string='Raw Meeting Transcript',
        help='Timestamped speech transcript captured during the meeting',
    )
    executive_summary = fields.Html()
    key_discussion_points = fields.Text()
    decisions = fields.Text(
        string='Decisions Made',
    )
    action_items = fields.Text(
        string='Action Items & To-Dos',
    )
    ai_provider = fields.Selection(
        [
            ('internal', 'Built-in Smart Summarizer'),
            ('openai', 'OpenAI'),
            ('ollama', 'Ollama / Local Engine'),
        ],
        string='AI Provider',
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
            'meeting_transcription_summary.ai_provider', 'internal'),
    )
    call_history_id = fields.Many2one(
        'discuss.call.history',
        string='Call',
        index='btree_not_null',
        ondelete='set null',
        help='The Discuss call this meeting was transcribed from',
    )
    transcribe_enabled = fields.Boolean(
        string='Transcribing',
        help='While the call runs: every participant\'s speech is recorded into this summary.',
    )
    transcript_line_ids = fields.One2many(
        'discuss.meeting.transcript.line',
        'summary_id',
        string='Transcript Lines',
    )
    state = fields.Selection(
        [
            ('live', 'Call in Progress'),
            ('processing', 'Transcribing Recording'),
            ('failed', 'Transcription Failed'),
            ('draft', 'Transcript Collected'),
            ('summarized', 'AI Summarized'),
            ('posted', 'Posted to Channel'),
        ],
        string='Status',
        default='draft',
    )
    # Uploaded recordings are transcribed in the background (see _cron_process_recordings)
    processing_error = fields.Text(string='Transcription Error', readonly=True)
    processing_start_dt = fields.Datetime(
        string='Transcription Started', readonly=True,
        help='When the background transcription job of the recording started; empty while queued',
    )
    transcription_engine = fields.Char(readonly=True)
    post_when_done = fields.Boolean(
        help='Post the summary to the channel as soon as the recording is transcribed',
    )
    requested_by_id = fields.Many2one(
        'res.users', readonly=True, ondelete='set null',
        help='Who queued the recording: notified when it is done, and author of the posted summary',
    )

    _call_history_unique = models.Constraint(
        'UNIQUE(call_history_id)',
        'A call can only have one meeting summary.',
    )

    @api.model
    def _get_live_meeting(self, channel, create=False):
        """The meeting of the call currently running in ``channel``, one per call for all participants.

        It is created when the call starts (``create``, from the rtc session that opened the call
        history), so transcription requests only ever look it up and never race to create it.
        """
        history = self.env['discuss.call.history'].sudo().search(
            [('channel_id', '=', channel.id), ('end_dt', '=', False)], limit=1)
        if not history:
            return self.browse()
        meeting = self.sudo().search([('call_history_id', '=', history.id)], limit=1)
        if not meeting and create:
            channel_title = channel.name or channel.display_name or self.env._("Call")
            meeting = self.sudo().create({
                'name': self.env._("Meeting: %s", channel_title),
                'channel_id': channel.id,
                'call_history_id': history.id,
                'date': history.start_dt,
                'state': 'live',
            })
        return meeting

    @api.model
    def _add_transcript_line(self, channel, member, speaker_name, text):
        """Record a final caption of the running call in ``channel``.

        Only while the call is being transcribed: subtitles alone leave nothing behind.
        """
        meeting = self._get_live_meeting(channel)
        if not meeting.transcribe_enabled:
            return
        self.env['discuss.meeting.transcript.line'].sudo().create({
            'summary_id': meeting.id,
            'channel_member_id': member.id,
            'speaker_name': speaker_name,
            'text': text.strip(),
        })

    def _is_call_running(self):
        """Whether the call this meeting records still goes on, whatever was done with its summary."""
        self.ensure_one()
        return bool(self.call_history_id) and not self.call_history_id.end_dt

    def _build_transcript(self):
        """The timestamped transcript of the lines recorded so far, in the current user's timezone."""
        self.ensure_one()
        return "\n".join(
            "[%s] %s: %s" % (
                fields.Datetime.context_timestamp(self, line.time).strftime('%H:%M:%S'),
                line.speaker_name,
                line.text,
            )
            for line in self.transcript_line_ids
        )

    def _finalize_live_meeting(self):
        """Called when the last participant left: build the transcript and invite to summarize.

        A call where nothing was transcribed leaves no meeting behind. A meeting already
        summarized or posted during the call only gets its full transcript and duration.
        """
        silent = self.filtered(lambda m: m.state == 'live' and not m.transcript_line_ids)
        silent.unlink()
        for meeting in self - silent:
            end_dt = meeting.call_history_id.end_dt or fields.Datetime.now()
            vals = {
                'raw_transcript': meeting._build_transcript(),
                'duration_minutes': max(1, round((end_dt - meeting.date).total_seconds() / 60)),
                'transcribe_enabled': False,
            }
            was_live = meeting.state == 'live'
            if was_live:
                vals['state'] = 'draft'
            meeting.write(vals)
            if was_live:
                meeting._post_call_ended_prompt()

    def action_transcribe_and_summarize(self):
        """Queue the uploaded video/audio file to be transcribed and summarized in the background.

        Transcribing a whole recording takes far longer than an HTTP request may run, so it
        happens in a detached job process, followed up by ``_cron_process_recordings``.
        """
        self.ensure_one()
        self._queue_recording_transcription()
        return True

    def _queue_recording_transcription(self, post=False):
        """Queue the recording; with ``post``, the summary is posted to the channel once ready."""
        self.ensure_one()
        if not self.recording_file:
            raise UserError(self.env._("Please upload a video or audio file first."))
        if self.state == 'processing':
            raise UserError(self.env._("This recording is already being transcribed."))
        get_param = self.env['ir.config_parameter'].sudo().get_param
        if (get_param('meeting_transcription_summary.stt_engine', 'whisper') == 'grok'
                and not get_param('meeting_transcription_summary.xai_api_key')):
            raise UserError(self.env._("Grok STT is the speech-to-text engine, but no xAI API key is set in "
                              "Settings > Discuss > Meeting Subtitles & AI Summaries."))
        self.write({
            'state': 'processing',
            'processing_error': False,
            'processing_start_dt': False,  # set once the cron starts the job
            'post_when_done': post,
            'requested_by_id': self.env.user.id,
        })
        self.env.ref('meeting_transcription_summary.ir_cron_process_recordings').sudo()._trigger()

    def _job_dir(self):
        self.ensure_one()
        return os.path.join(config['data_dir'], 'meeting_stt_jobs', self.env.cr.dbname, str(self.id))

    def _start_recording_job(self):
        """Start the detached transcription process of this queued recording."""
        self.ensure_one()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        engine = 'grok' if get_param('meeting_transcription_summary.stt_engine', 'whisper') == 'grok' else 'whisper'
        keywords = [k.strip() for k in (get_param('meeting_transcription_summary.keywords', '') or '')
                    .replace('\n', ',').split(',') if k.strip()]
        keywords += [n for n in self.attendee_ids.mapped('name') if n and n not in keywords]
        request = {
            'engine': engine,
            'language': get_param('meeting_transcription_summary.subtitles_language', 'en-US'),
            'model': get_param('meeting_transcription_summary.whisper_model', 'small'),
            'main_language': get_param('meeting_transcription_summary.main_language', 'en-US'),
            'keywords': keywords[:30],
        }
        if engine == 'grok':
            request['api_key'] = get_param('meeting_transcription_summary.xai_api_key', '')
        stt_client.start_job(self._job_dir(), request, base64.b64decode(self.recording_file),
                             self.recording_filename or "recording.mp4")
        self.write({'transcription_engine': engine, 'processing_start_dt': fields.Datetime.now()})

    @api.model
    def _cron_process_recordings(self):
        """Start queued recording jobs and complete the finished ones.

        Polls again shortly while any job runs. At most one local Whisper job runs at a time
        (it saturates the CPU); cloud jobs only wait on xAI.
        """
        IrCron = self.env['ir.cron']
        processing = self.search([('state', '=', 'processing')], order='id')
        running = {'whisper': 0, 'grok': 0}
        for meeting in processing.filtered('processing_start_dt'):
            status, data = stt_client.job_status(meeting._job_dir())
            if status == 'running':
                if fields.Datetime.now() - meeting.processing_start_dt > RECORDING_JOB_MAX_DURATION:
                    stt_client.cancel_job(meeting._job_dir())
                    meeting._fail_recording(self.env._("Transcription took longer than %s hours and was stopped.",
                                              int(RECORDING_JOB_MAX_DURATION.total_seconds() // 3600)))
                else:
                    running[meeting.transcription_engine or 'whisper'] += 1
                    continue
            elif status == 'done':
                meeting._complete_recording_job(data)
            else:
                meeting._complete_recording_job({'error': data})
            IrCron._commit_progress(1)
        for meeting in processing.filtered(lambda m: not m.processing_start_dt):
            engine = 'grok' if self.env['ir.config_parameter'].sudo().get_param(
                'meeting_transcription_summary.stt_engine', 'whisper') == 'grok' else 'whisper'
            if running[engine] >= MAX_RUNNING_JOBS[engine]:
                continue
            try:
                meeting._start_recording_job()
                running[engine] += 1
            except Exception as exc:
                _logger.exception("Could not start the transcription of meeting %s", meeting.id)
                meeting._fail_recording(self.env._("Could not start the transcription: %s", exc))
            IrCron._commit_progress(1)
        if self.search_count([('state', '=', 'processing')]):
            self.env.ref('meeting_transcription_summary.ir_cron_process_recordings')._trigger(
                fields.Datetime.now() + RECORDING_JOB_POLL)

    def _complete_recording_job(self, result):
        """Store the transcript of a finished job, then summarize (and post) it."""
        self.ensure_one()
        stt_client.cancel_job(self._job_dir())  # the job is over: only removes its files
        text = (result.get('text') or '').strip()
        error = result.get('error')
        if error:
            _logger.warning("Transcription job of meeting %s failed: %s", self.id, error)
        if not text and error and self.transcription_engine != 'grok':
            # local Whisper missing or failed (not a recording it heard nothing in): the OpenAI
            # Whisper API, if the admin opted in to the fallback
            try:
                text = self._transcribe_with_openai()
            except UserError as exc:
                error = str(exc)
            if not text and (not error or error.startswith('not_installed')):
                error = error and self.env._(
                    "To transcribe uploaded audio/video recordings without OpenAI, install the free local "
                    "engine on your Odoo server:\n   pip install faster-whisper\n(100% free and runs offline "
                    "on your CPU/GPU).\n\nAlternatively, choose Grok STT as the engine with an xAI API Key, or "
                    "provide an OpenAI API Key and enable OpenAI Speech Fallback, in Settings > Discuss > Meeting Subtitles & AI Summaries.")
        if not text:
            if error and self.transcription_engine == 'grok':
                error = self.env._("Grok STT could not transcribe the recording: %s", error)
            self._fail_recording(error or self.env._("Could not transcribe any speech from the uploaded file. "
                                            "Ensure the audio is audible."))
            return
        vals = {'raw_transcript': text, 'state': 'draft'}
        if result.get('duration'):
            vals['duration_minutes'] = max(1, round(result['duration'] / 60))
        self.write(vals)
        # summarize and post as the uploader: the summary is posted under their name
        meeting = self.with_user(self.requested_by_id) if self.requested_by_id.active else self
        try:
            with self.env.cr.savepoint():
                meeting.action_generate_summary()
                if self.post_when_done:
                    meeting.action_post_to_channel()
        except Exception as exc:
            _logger.exception("Summarizing the recording of meeting %s failed", self.id)
            self._notify_requester('warning', self.env._(
                "The recording \"%(name)s\" was transcribed, but summarizing it failed: %(error)s",
                name=self.name, error=exc))
            return
        if self.post_when_done:
            message = self.env._("The recording \"%(name)s\" was transcribed and its summary posted to %(channel)s.",
                        name=self.name, channel=self.channel_id.display_name)
        else:
            message = self.env._("The recording \"%s\" was transcribed and summarized.", self.name)
        self._notify_requester('success', message)

    def _fail_recording(self, reason):
        self.ensure_one()
        self.write({'state': 'failed', 'processing_error': reason})
        self._notify_requester('danger', self.env._(
            "The recording \"%(name)s\" could not be transcribed: %(error)s", name=self.name, error=reason))

    def _notify_requester(self, notification_type, message):
        if self.requested_by_id:
            self.requested_by_id.partner_id._bus_send("simple_notification", {
                'type': notification_type,
                'title': self.env._("Meeting Recording"),
                'message': message,
                'sticky': notification_type != 'success',
            })

    def _transcribe_with_openai(self):
        """The recording's transcript from the OpenAI Whisper API, or '' when the fallback is off
        or no key is configured (the key alone may be there for summaries only)."""
        get_param = self.env['ir.config_parameter'].sudo().get_param
        api_key = get_param('meeting_transcription_summary.openai_api_key', '')
        if not api_key or get_param('meeting_transcription_summary.stt_openai_fallback') not in ('True', '1'):
            return ''
        language = get_param('meeting_transcription_summary.subtitles_language', 'en-US')
        files = {
            'file': (self.recording_filename or "recording.mp4", base64.b64decode(self.recording_file)),
            'model': (None, 'whisper-1'),
        }
        if language and language != 'auto':
            files['language'] = (None, language.split('-')[0])
        try:
            res = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                timeout=(10, 90),  # runs in the cron: must end well within its time limit
            )
        except requests.RequestException as exc:
            raise UserError(self.env._("Whisper transcription failed: %s", exc))
        if res.status_code != 200:
            _logger.warning("Whisper transcription failed: %s", res.text)
            raise UserError(self.env._("Whisper transcription failed: %s", res.text[:300]))
        return res.json().get('text', '').strip()

    def unlink(self):
        job_dirs = [meeting._job_dir() for meeting in self if meeting.state == 'processing']
        res = super().unlink()
        for job_dir in job_dirs:
            stt_client.cancel_job(job_dir)
        return res

    def action_generate_and_post_summary(self):
        """Generates summary if needed, and posts it to the channel chatter, once.

        Every participant gets the same "Generate AI Summary Now" link: whoever clicks first
        posts the summary, later clicks change nothing.
        """
        self.ensure_one()
        # Serialize concurrent clicks: a click that waited here sees the first one's result
        # (it is retried after the first commits), so it does not post a second copy.
        self.env.cr.execute("SELECT id FROM discuss_meeting_summary WHERE id = %s FOR UPDATE", [self.id])
        if self.state == 'posted':
            return True
        if self.state in ('live', 'draft') or not self.executive_summary:
            self.action_generate_summary()
        self.action_post_to_channel()
        return True

    def action_generate_summary(self):
        """Generates AI meeting summary based on raw transcript."""
        self.ensure_one()
        call_running = self._is_call_running()
        if call_running or self.state == 'live':
            # summarizing during the call (even after a summary was posted): use everything said so far
            self.raw_transcript = self._build_transcript()
        if not self.raw_transcript or not self.raw_transcript.strip():
            raise UserError(self.env._("The meeting transcript is empty. Speak or add transcript text before summarizing."))

        # Read provider settings from general config
        get_param = self.env['ir.config_parameter'].sudo().get_param
        configured_provider = get_param('meeting_transcription_summary.ai_provider', 'internal')
        provider = self.ai_provider or configured_provider

        summary_data = None
        if provider == 'openai':
            api_key = get_param('meeting_transcription_summary.openai_api_key', '')
            model = get_param('meeting_transcription_summary.openai_model', 'gpt-4o-mini')
            if api_key:
                try:
                    summary_data = self._call_openai(self.raw_transcript, api_key, model)
                except Exception as e:
                    _logger.warning("OpenAI summarization failed, falling back to built-in summarizer: %s", e)

        elif provider == 'ollama':
            endpoint = get_param('meeting_transcription_summary.ollama_endpoint', 'http://localhost:11434')
            model = get_param('meeting_transcription_summary.ollama_model', 'llama3')
            try:
                summary_data = self._call_ollama(self.raw_transcript, endpoint, model)
            except Exception as e:
                _logger.warning("Ollama summarization failed, falling back to built-in summarizer: %s", e)

        # Fallback to smart built-in summarizer if external AI was not used or failed
        if not summary_data:
            summary_data = self._builtin_summarize(self.raw_transcript)

        self.write({
            'executive_summary': summary_data.get('executive_summary', ''),
            'key_discussion_points': summary_data.get('key_discussion_points', ''),
            'decisions': summary_data.get('decisions', ''),
            'action_items': summary_data.get('action_items', ''),
            # a running call stays live: its full transcript is summarized again when it ends
            'state': 'live' if call_running else 'summarized',
        })
        return True

    def action_post_to_channel(self):
        """Posts the formatted meeting summary directly into the channel chatter with rich HTML styling."""
        self.ensure_one()
        if self.state == 'posted':
            # refreshing the summary makes it postable again
            raise UserError(self.env._("This summary has already been posted to the channel."))

        def lines(text):
            return [line.strip() for line in (text or "").split("\n") if line.strip()]

        body = self.env["ir.qweb"]._render("meeting_transcription_summary.meeting_summary_message", {
            "meeting_name": self.name or (self.channel_id.name and self.env._("Meeting: %s", self.channel_id.name))
            or self.env._("Discuss Meeting"),
            "duration": self.duration_minutes,
            "when": self._summary_time_range(),
            "attendees": [{"name": name, "initials": "".join(word[0] for word in name.split()[:2]).upper()}
                          for name in self.attendee_ids.mapped("name") if name],
            "overview": self.executive_summary,
            "points": lines(self.key_discussion_points),
            "decisions": lines(self.decisions),
            "actions": lines(self.action_items),
            "view_url": self._form_url(),
        })
        self.channel_id.message_post(
            body=body,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        self.state = 'posted'
        return True

    def _form_url(self):
        return f"{self.get_base_url()}/web#id={self.id}&model=discuss.meeting.summary&view_type=form"

    def _summary_time_range(self):
        """"Oct 27, 2026 · 12:52 – 1:50 PM", in the reader's language and timezone."""
        start = fields.Datetime.context_timestamp(self, self.date)
        end = start + timedelta(minutes=self.duration_minutes or 0)
        locale = babel_locale_parse(get_lang(self.env).code)
        # 12- or 24-hour clock as the language writes times
        skeleton = "hm" if "a" in locale.time_formats["short"].pattern else "Hm"
        return "%s · %s" % (format_date(start, "medium", locale=locale),
                            format_interval(start, end, skeleton, tzinfo=start.tzinfo, locale=locale))

    def _post_call_ended_prompt(self):
        """Posts an interactive notification card in the channel chatter when a call finishes,
        allowing participants to click 'Generate AI Summary' with 1 click."""
        self.ensure_one()
        base_url = self.get_base_url()
        body = self.env["ir.qweb"]._render("meeting_transcription_summary.meeting_ended_message", {
            "duration": self.duration_minutes,
            "lines_count": len([line for line in (self.raw_transcript or "").split("\n") if line.strip()]),
            "generate_url": f"{base_url}/discuss/meeting/generate_summary_redirect?summary_id={self.id}",
            "view_url": self._form_url(),
        })
        # Posted by OdooBot: the call ends with whoever leaves last, possibly a guest or the
        # inactive-session cleanup, so no participant is the natural author.
        self.channel_id.sudo().message_post(
            body=body,
            author_id=self.env.ref('base.partner_root').id,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        return True

    def _call_openai(self, transcript, api_key, model='gpt-4o-mini'):
        """Queries OpenAI API for meeting summarization with deduplication prompt."""
        system_prompt = (
            "You are an expert executive meeting assistant. Analyze the provided meeting transcript. "
            "Note: speech-to-text transcripts may contain repetition and transcription noise. "
            "Filter out duplicate phrases and synthesize a clean, professional summary. "
            "Output a strictly formatted JSON object with keys:\n"
            "- executive_summary: A concise HTML paragraph summarizing the core discussion.\n"
            "- key_discussion_points: Newline-separated list of key topics discussed (no duplicates).\n"
            "- decisions: Newline-separated list of agreed decisions or alignments.\n"
            "- action_items: Newline-separated list of actionable tasks with owners (e.g. 'John to review PR')."
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Meeting Transcript:\n{transcript}"},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        return self._parse_llm_summary(content)

    def _call_ollama(self, transcript, endpoint='http://localhost:11434', model='llama3'):
        """Queries Ollama local model instance for meeting summarization."""
        url = endpoint.rstrip('/') + '/api/chat'
        prompt = (
            "You are an AI meeting assistant. Analyze this transcript, remove duplicate speech recognition text, "
            "and return a valid JSON object with keys: executive_summary, key_discussion_points, decisions, action_items.\n\n"
            f"Transcript:\n{transcript}"
        )
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
        }

        response = requests.post(url, json=payload, timeout=40)
        response.raise_for_status()
        content = response.json().get('message', {}).get('content', '{}')
        return self._parse_llm_summary(content)

    @api.model
    def _parse_llm_summary(self, content):
        """Turn the JSON an LLM returned into field values.

        Models often answer the list sections with JSON arrays (or a single string) whatever the
        prompt says: every list ends up as one item per line, and the overview as escaped text.
        """
        parsed = json.loads(content)

        def as_lines(value):
            if isinstance(value, (list, tuple)):
                return "\n".join(str(item).strip() for item in value if str(item).strip())
            return str(value or '').strip()

        overview = parsed.get('executive_summary') or ''
        if isinstance(overview, (list, tuple)):
            overview = " ".join(str(item) for item in overview)
        # the overview may already be the requested HTML paragraph; anything else is plain text
        overview = str(overview).strip()
        if not overview.startswith('<'):
            overview = Markup("<p>%s</p>") % overview
        return {
            'executive_summary': overview,
            'key_discussion_points': as_lines(parsed.get('key_discussion_points')),
            'decisions': as_lines(parsed.get('decisions')),
            'action_items': as_lines(parsed.get('action_items')),
        }

    @api.model
    def _builtin_action_item(self, speaker, sentence):
        """The action item ``sentence`` states, labelled with its owner, or None.

        A task is a request to someone ("Arun, can you check the server?"), a promise by a person
        ("I'll send it", "Priya is going to call them") or a task phrase ("we need to", "by Friday",
        "next step"). "Will" or "must" alone is no task: "It will rain" and "This must be the old
        version" stay key points.
        """
        sentence = sentence.replace('\u2019', "'")  # speech engines write "I’ll" as often as "I'll"
        if CALL_CHECK_RE.search(sentence):
            return None
        request = REQUEST_RE.search(sentence)
        if request:
            # the owner is the person asked, when named ("Arun, can you…" / "…, Arun?")
            end = REQUEST_ADDRESSEE_END_RE.search(sentence)
            addressee = request.group(1) or (end and end.group(1))
            if addressee and addressee.lower() not in NOT_AN_ADDRESSEE:
                if request.group(1):
                    task = sentence[request.start(0) + len(addressee):].lstrip(', ')
                else:
                    task = sentence[:end.start()] + sentence[end.end(1):].strip()
                task = task[0].upper() + task[1:]
                asked_by = f" ({self.env._('asked by %s', speaker)})" if speaker else ""
                return f"{addressee}: {task}{asked_by}"
            return f"{speaker}: {sentence}" if speaker else sentence

        promised = any(
            subject.lower() in PERSON_PRONOUNS
            or (subject[0].isupper() and subject.lower() not in NOT_A_PERSON)
            for subject in COMMITMENT_RE.findall(sentence))
        if not promised and not ACTION_PHRASE_RE.search(sentence):
            return None
        # "I will send it" -> "Speaker: Will send it"
        sentence = SELF_COMMITMENT_RE.sub('Will ', sentence)
        return f"{speaker}: {sentence}" if speaker else sentence

    def _builtin_summarize(self, transcript):
        """Intelligent heuristic summarizer that removes duplicate lines,
        extracts clean discussion topics, decisions, and action items.
        """
        lines = [line.strip() for line in transcript.split("\n") if line.strip()]
        speakers = set()
        parsed_entries = []

        for line in lines:
            # format: "[10:20:30] Name: text" or "Name: text"; a name is short and holds no sentence,
            # so a colon further into a plain sentence does not make a speaker of it
            match = re.match(r'(?:\[\d{2}:\d{2}:\d{2}\]\s*)?([^:.!?]{1,60}):\s*(.*)', line)
            speaker, text = (match.group(1).strip(), match.group(2)) if match else ("", line)
            if speaker:
                speakers.add(speaker)
            # One entry per sentence: a transcribed recording comes as a single line of plain text
            # (Whisper, or Grok with one voice), which would otherwise become one huge bullet.
            for sentence in re.split(r'(?<=[.!?])\s+', text.strip()):
                if sentence:
                    parsed_entries.append((speaker, sentence))

        # Deduplication of identical and consecutive speech repetitions
        clean_entries = []
        seen_normalized = set()
        for speaker, text in parsed_entries:
            norm = re.sub(r'[^\w\s]', '', text.lower()).strip()
            if not norm or norm in seen_normalized:
                continue
            seen_normalized.add(norm)
            clean_entries.append((speaker, text))

        key_points = []
        decisions = []
        action_items = []

        # phrases that state a decision or a task, not mere assent ("yes", "perfect") or chatter
        decision_words = ['agree', 'agreed', 'decide', 'decided', 'approve', 'approved', 'confirm', 'confirmed',
                          'resolution', "let's go with", 'go ahead with']

        for speaker, text in clean_entries:
            lower = text.lower()
            clean_sentence = text[0].upper() + text[1:] if len(text) > 1 else text
            if not clean_sentence.endswith(('.', '!', '?')):
                clean_sentence += '.'

            action = self._builtin_action_item(speaker, clean_sentence)
            if action:
                action_items.append(action)
            # Check for decisions
            elif any(re.search(rf'\b{w}\b', lower) for w in decision_words):
                item_label = f"{speaker}: {clean_sentence}" if speaker else clean_sentence
                decisions.append(item_label)
            else:
                item_label = f"{speaker}: {clean_sentence}" if speaker else clean_sentence
                key_points.append(item_label)

        # Meeting minutes only report what was said: a section with nothing found stays empty
        # (and is left out of the posted card) rather than being filled with invented text.
        if not key_points and clean_entries:
            key_points = [f"{s}: {t}" if s else t for s, t in clean_entries[:4]]

        # Create natural, understandable overview paragraph
        speakers_str = ", ".join(speakers) if speakers else self.env._("Participants")
        topic_highlights = [t for _speaker, t in clean_entries[:3]]
        topics_str = ", ".join([f'"{th}"' for th in topic_highlights])

        if topic_highlights:
            overview_text = Markup(
                "The meeting was attended by <strong>%s</strong>. "
                "The team discussed live topics including %s. "
                "Key discussion highlights and next steps were captured below.",
            ) % (speakers_str, topics_str)
        else:
            overview_text = Markup(
                "Meeting with <strong>%s</strong>. "
                "Discussion points and actionable next steps were documented.",
            ) % speakers_str

        return {
            'executive_summary': Markup("<p>%s</p>") % overview_text,
            'key_discussion_points': "\n".join(key_points),
            'decisions': "\n".join(decisions),
            'action_items': "\n".join(action_items),
        }
