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

"""Client for Grok STT, the speech-to-text API of xAI (https://docs.x.ai, ``POST /v1/stt``).

Runs in the cloud: no model on the Odoo server, and each request is independent, so calls
never queue behind each other as they do with the local speech worker.
"""
import logging
import re

import requests

_logger = logging.getLogger(__name__)

ENDPOINT = "https://api.x.ai/v1/stt"
MODEL = "grok-voice-transcribe-2.0"
MAX_FILE_BYTES = 500 * 1024 * 1024
MAX_KEYTERMS = 100
MAX_KEYTERM_CHARS = 50
# languages Grok STT accepts: a bare code, or one of the regional variants it lists
LANGUAGES = {
    "ar", "bs", "bg", "yue", "ca", "zh", "hr", "cs", "da", "nl", "en", "fil", "fi", "fr", "de", "el",
    "hi", "hu", "id", "it", "ja", "ko", "mk", "ms", "nb", "fa", "pl", "pt", "ro", "ru", "sk", "es",
    "sv", "th", "tr", "uk", "ur", "vi",
}
REGIONAL_LANGUAGES = {"es-ES", "pt-PT", "ar-AE", "ar-SA"}
# written-form formatting (numbers, dates...) only exists for these
FORMAT_LANGUAGES = {"ar", "zh", "en", "fr", "de", "ja", "pt", "ru", "es", "sv", "vi"}
SPACE_BEFORE_PUNCTUATION = re.compile(r"\s+([,.!?;:%])")
# kept open between captions: a new TLS handshake per request costs a few hundred ms
_session = requests.Session()


class GrokSttError(Exception):
    """The Grok STT request failed or was rejected.

    ``kind`` tells why, to explain it to the speaker: 'rate_limit', 'auth', 'timeout',
    'unreachable', 'too_large' or 'error'; ``status`` is the HTTP status, if any.
    """

    def __init__(self, message, kind="error", status=None):
        super().__init__(message)
        self.kind = kind
        self.status = status


def grok_language(language):
    """The code Grok STT understands for a setting like 'en-US', or None to auto-detect."""
    if not language or language == "auto":
        return None
    if language in REGIONAL_LANGUAGES:
        return language
    base = language.split("-")[0].lower()
    return base if base in LANGUAGES else None


def transcribe(audio_bytes, api_key, filename="audio.wav", language=None, keywords=None,
               diarize=False, timeout=30):
    """Transcribe audio with Grok STT.

    Container formats (wav, mp3, ogg, webm/opus, mp4, mkv...) are detected by the API.
    Returns its JSON reply: ``{"text", "language", "duration", "words": [{"text", "start",
    "end", "speaker"?}]}``. Raises GrokSttError when the request fails.
    """
    if len(audio_bytes) > MAX_FILE_BYTES:
        raise GrokSttError("the file is larger than the 500 MB Grok STT accepts", "too_large")
    data = [("model", MODEL)]
    lang = grok_language(language)
    if lang:
        data.append(("language", lang))
        if lang.split("-")[0] in FORMAT_LANGUAGES:
            data.append(("format", "true"))
    if diarize:
        data.append(("diarize", "true"))
    terms = [k.strip()[:MAX_KEYTERM_CHARS] for k in keywords or [] if k and k.strip()]
    data += [("keyterm", term) for term in dict.fromkeys(terms)][:MAX_KEYTERMS]
    try:
        # requests writes the form fields before the file, as the API requires
        response = _session.post(
            ENDPOINT,
            headers={"Authorization": "Bearer %s" % api_key},
            data=data,
            files={"file": (filename, audio_bytes)},
            timeout=timeout,
        )
    except requests.Timeout as exc:
        raise GrokSttError("Grok STT did not answer in time: %s" % exc, "timeout") from exc
    except requests.RequestException as exc:
        raise GrokSttError("Grok STT is unreachable: %s" % exc, "unreachable") from exc
    if response.status_code != 200:
        try:
            detail = response.json()
        except ValueError:
            detail = None
        if isinstance(detail, dict):
            detail = detail.get("error") or detail
        if isinstance(detail, dict):
            detail = detail.get("message") or detail
        detail = detail or response.text
        kind = {429: "rate_limit", 401: "auth", 403: "auth"}.get(response.status_code, "error")
        raise GrokSttError("Grok STT returned %s: %s" % (response.status_code, str(detail)[:300]),
                           kind, response.status_code)
    try:
        return response.json()
    except ValueError as exc:
        raise GrokSttError("Grok STT returned an unreadable reply") from exc


def _timestamp(seconds):
    seconds = int(seconds or 0)
    return "%02d:%02d:%02d" % (seconds // 3600, seconds % 3600 // 60, seconds % 60)


def speaker_transcript(result):
    """A "[HH:MM:SS] Speaker N: text" line per speaker turn, from a diarized reply.

    Falls back to the plain text when the reply has no speakers (a single voice, or no words).
    """
    words = [w for w in result.get("words") or [] if (w.get("text") or "").strip()]
    if not words or len({w.get("speaker") for w in words} - {None}) < 2:
        return (result.get("text") or "").strip()
    turns = []
    for word in words:
        speaker = word.get("speaker")
        if not turns or turns[-1]["speaker"] != speaker:
            turns.append({"speaker": speaker, "start": word.get("start"), "words": []})
        turns[-1]["words"].append(word["text"].strip())
    lines = []
    for turn in turns:
        text = SPACE_BEFORE_PUNCTUATION.sub(r"\1", " ".join(turn["words"]))
        name = "Speaker %d" % (turn["speaker"] + 1) if isinstance(turn["speaker"], int) else "Speaker"
        lines.append("[%s] %s: %s" % (_timestamp(turn["start"]), name, text))
    return "\n".join(lines)
