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

"""Client for Whisper behind an OpenAI-compatible API (``POST <url>/audio/transcriptions``).

The same request works with OpenAI, Groq, Fireworks or DeepInfra, and with a Whisper server of
your own on a GPU (e.g. speaches). Like Grok STT it runs elsewhere: no model on the Odoo server,
and each request is independent, so captions never queue behind each other.
"""
import logging
from types import SimpleNamespace

import requests

from . import stt_worker

_logger = logging.getLogger(__name__)

DEFAULT_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "whisper-large-v3"
MAX_FILE_BYTES = 25 * 1024 * 1024  # OpenAI's limit, and Groq's on its free tier
# Whisper reads at most 224 prompt tokens: names and terms beyond that are cut anyway
MAX_PROMPT_CHARS = 800
# verbose_json names the language ("english"); the browser expects its code
LANGUAGE_CODES = {
    "english": "en", "spanish": "es", "french": "fr", "german": "de", "italian": "it",
    "dutch": "nl", "polish": "pl", "portuguese": "pt", "hindi": "hi", "malayalam": "ml",
    "tamil": "ta", "arabic": "ar", "russian": "ru", "chinese": "zh", "japanese": "ja",
    "korean": "ko", "turkish": "tr", "ukrainian": "uk", "swedish": "sv", "telugu": "te",
    "kannada": "kn", "bengali": "bn", "marathi": "mr", "urdu": "ur",
}
# kept open between captions: a new TLS handshake per request costs a few hundred ms
_session = requests.Session()


class CloudWhisperError(Exception):
    """The request failed or was rejected.

    ``kind`` tells why, to explain it to the speaker: 'rate_limit', 'auth', 'timeout',
    'unreachable', 'too_large' or 'error'; ``status`` is the HTTP status, if any.
    """

    def __init__(self, message, kind="error", status=None):
        super().__init__(message)
        self.kind = kind
        self.status = status


def _language_code(name):
    name = (name or "").strip().lower()
    return name if len(name) in (2, 3) and name.isalpha() else LANGUAGE_CODES.get(name)


def transcribe(audio_bytes, api_key=None, url=DEFAULT_URL, model=DEFAULT_MODEL, filename="audio.wav",
               language=None, keywords=None, timeout=15):
    """Transcribe audio with a Whisper model behind an OpenAI-compatible API.

    ``language`` is a setting like 'en-US' ('auto' or None to detect it). ``keywords`` become the
    prompt, as the local Whisper takes them as hotwords. Segments the model itself flags as
    unreliable, and its stock phrases on noise ("Thank you."), are dropped as with local Whisper.
    Returns ``{"text", "language"}``. Raises CloudWhisperError when the request fails.
    """
    if len(audio_bytes) > MAX_FILE_BYTES:
        raise CloudWhisperError("the audio is larger than the 25 MB these APIs accept", "too_large")
    data = {"model": model or DEFAULT_MODEL, "response_format": "verbose_json", "temperature": "0"}
    if language and language != "auto":
        data["language"] = language.split("-")[0].lower()
    terms = list(dict.fromkeys(k.strip() for k in keywords or [] if k and k.strip()))
    if terms:
        data["prompt"] = ", ".join(terms)[:MAX_PROMPT_CHARS]
    endpoint = (url or DEFAULT_URL).rstrip("/") + "/audio/transcriptions"
    try:
        response = _session.post(
            endpoint,
            headers={"Authorization": "Bearer %s" % api_key} if api_key else {},
            data=data,
            files={"file": (filename, audio_bytes)},
            timeout=timeout,
        )
    except requests.Timeout as exc:
        raise CloudWhisperError("%s did not answer in time: %s" % (endpoint, exc), "timeout") from exc
    except requests.RequestException as exc:
        raise CloudWhisperError("%s is unreachable: %s" % (endpoint, exc), "unreachable") from exc
    if response.status_code != 200:
        try:
            detail = response.json()
        except ValueError:
            detail = None
        # usually {"error": {"message": ...}}, but a proxy or a server of your own may say it otherwise
        if isinstance(detail, dict):
            detail = detail.get("error") or detail
        if isinstance(detail, dict):
            detail = detail.get("message") or detail
        detail = detail or response.text
        kind = {429: "rate_limit", 401: "auth", 403: "auth"}.get(response.status_code, "error")
        raise CloudWhisperError("%s returned %s: %s" % (endpoint, response.status_code, str(detail)[:300]),
                                kind, response.status_code)
    try:
        reply = response.json()
    except ValueError as exc:
        raise CloudWhisperError("%s returned an unreadable reply" % endpoint) from exc
    segments = [SimpleNamespace(
        text=(s.get("text") or "").strip(),
        no_speech_prob=s.get("no_speech_prob") or 0.0,
        avg_logprob=s.get("avg_logprob") or 0.0,
        compression_ratio=s.get("compression_ratio") or 0.0,
    ) for s in reply.get("segments") or []]
    if segments:
        reliable = [s for s in segments if stt_worker.is_reliable(s)]
        text = stt_worker.clean_text(" ".join(s.text for s in reliable),
                                     keep_known=bool(reliable) and all(stt_worker.is_confident(s) for s in reliable))
    else:
        # a server that gives no segments: nothing tells its stock phrases from real ones
        text = stt_worker.clean_text(reply.get("text") or "")
    return {"text": text, "language": _language_code(reply.get("language"))}
