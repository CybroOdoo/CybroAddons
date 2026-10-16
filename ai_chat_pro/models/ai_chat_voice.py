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
import io
import logging
import re
import time
import wave

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

CHAT_COMPLETIONS_ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
MODELS_ENDPOINT = 'https://openrouter.ai/api/v1/models'
DEFAULT_VOICE_MODEL = 'google/gemini-2.5-flash-lite'
# the web client sends 16 kHz mono 16-bit PCM: sent as a WAV file, a format all providers read
VOICE_SAMPLE_RATE = 16000
MAX_VOICE_SECONDS = 120
# the models of OpenRouter that read audio, listed once an hour: (time read, models)
VOICE_MODELS_CACHE_SECONDS = 3600
_VOICE_MODELS_CACHE = {}
TRANSCRIBE_PROMPT = (
    "Transcribe this recording of a user asking a business software assistant a question or a request. Write "
    "exactly what is said, in the language it is said in, with punctuation. Reply with the transcription only: "
    "no quotes, no comment, no translation. Reply with nothing if nobody speaks."
)


def get_voice_models():
    """ The models of OpenRouter turning speech into text: those reading audio and
    writing text, cheapest first, as ``(id, label)``. Read from OpenRouter once an
    hour; an empty list when it can not be reached. """
    read_at, voice_models = _VOICE_MODELS_CACHE.get('models', (0, None))
    if voice_models is not None and time.time() - read_at < VOICE_MODELS_CACHE_SECONDS:
        return voice_models
    try:
        response = requests.get(MODELS_ENDPOINT, timeout=10)
        response.raise_for_status()
        data = response.json().get('data') or []
    except (requests.RequestException, ValueError) as error:
        _logger.info("AI Chat Pro: the models of OpenRouter could not be read: %s", error)
        return voice_models or []
    found = []
    for model in data:
        architecture = model.get('architecture') or {}
        pricing = model.get('pricing') or {}
        # batch models answer later, through another API: no use while the user waits
        if model['id'].endswith(':batch'):
            continue
        try:
            # per million tokens: the price of audio when the model has one, else of any input;
            # negative for routers, whose price depends on the model they pick
            price = float(pricing.get('audio') or pricing.get('prompt') or 0) * 1e6
        except (TypeError, ValueError):
            continue
        if (
            'audio' not in (architecture.get('input_modalities') or [])
            or 'text' not in (architecture.get('output_modalities') or []) or price < 0
        ):
            continue
        name = model.get('name') or model['id']
        if not price:
            label = name if 'free' in name.lower() else f"{name} (free)"
        else:
            unit = "audio" if pricing.get('audio') else "input"
            label = f"{name} (${price:.2f} / M {unit} tokens)"
        found.append((price, model['id'], label))
    voice_models = [(model_id, label) for _price, model_id, label in sorted(found)]
    _VOICE_MODELS_CACHE['models'] = (time.time(), voice_models)
    return voice_models


def get_voice_model(env):
    """ The speech to text model chosen in the settings. A name without provider is a
    Whisper model of a former version of the module, run on the server: the default
    model replaces it. """
    model_id = env['ir.config_parameter'].sudo().get_str('ai_chat_pro.voice_model')
    return model_id if '/' in model_id else DEFAULT_VOICE_MODEL


class AiChatTranscription(models.Model):
    """ A voice question turned into text, and what it cost: shown apart from the
    answers in the usage of the assistant. """
    _name = 'ai.chat.transcription'
    _description = "AI Chat Voice Transcription"
    _order = 'id desc'

    user_id = fields.Many2one('res.users', required=True, index=True, ondelete='cascade',
                              default=lambda self: self.env.user)
    ai_model = fields.Char(string="Model")
    seconds = fields.Float(digits=(16, 1), help="Length of the recording.")
    prompt_tokens = fields.Integer()
    completion_tokens = fields.Integer()
    cost = fields.Float(digits=(16, 6), help="Cost reported by OpenRouter, in credits (USD).")


class AiChatAssistant(models.AbstractModel):
    """ Voice questions, turned into text by a model of OpenRouter reading audio, with
    the key of the assistant. """
    _inherit = 'ai.chat.assistant'

    @api.model
    def _transcribe(self, audio):
        """ Turn a recorded question into text.

        :param bytes audio: the recording, as 16 kHz mono 16-bit PCM
        :return: the text said
        """
        if not audio or len(audio) % 2:
            raise UserError(self.env._("Nothing was recorded. Please try again."))
        if len(audio) > MAX_VOICE_SECONDS * VOICE_SAMPLE_RATE * 2:
            raise UserError(self.env._("The recording is too long. Please ask a shorter question."))
        ai_model = get_voice_model(self.env)
        usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0.0, 'ai_called': False}
        data = self._openrouter_post(CHAT_COMPLETIONS_ENDPOINT, {
            'model': ai_model,
            'messages': [{'role': 'user', 'content': [
                {'type': 'text', 'text': TRANSCRIBE_PROMPT},
                {'type': 'input_audio', 'input_audio': {'data': _to_wav_base64(audio), 'format': 'wav'}},
            ]}],
            'temperature': 0,
            'max_tokens': 1000,
            'usage': {'include': True},
            'user': str(self.env.uid),
        }, usage)
        tokens = data.get('usage') or {}
        # the recording is paid for, even when nothing is heard
        self.env['ai.chat.transcription'].sudo().create({
            'user_id': self.env.uid,
            'ai_model': ai_model,
            'seconds': len(audio) / (VOICE_SAMPLE_RATE * 2),
            'prompt_tokens': int(tokens.get('prompt_tokens') or 0),
            'completion_tokens': int(tokens.get('completion_tokens') or 0),
            'cost': float(tokens.get('cost') or 0.0),
        })
        choices = data.get('choices') or [{}]
        text = ((choices[0].get('message') or {}).get('content')) or ''
        if isinstance(text, list):
            # some providers answer content parts
            text = ' '.join(part.get('text') or '' for part in text if isinstance(part, dict))
        return _clean_transcription(text)

    @api.model
    def _get_voice_usage(self, domain):
        """ The recordings turned into text matching a domain, their length and cost. """
        [(seconds, prompt, completion, cost, count)] = self.env['ai.chat.transcription'].sudo()._read_group(
            domain, aggregates=['seconds:sum', 'prompt_tokens:sum', 'completion_tokens:sum', 'cost:sum', '__count'],
        )
        return {
            'recordings': count,
            'seconds': seconds or 0.0,
            'tokens': (prompt or 0) + (completion or 0),
            'cost': cost or 0.0,
        }


def _to_wav_base64(pcm):
    """ 16 kHz mono 16-bit PCM, as a WAV file in base64. """
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(VOICE_SAMPLE_RATE)
        wav.writeframes(pcm)
    return base64.b64encode(output.getvalue()).decode()


def _clean_transcription(text):
    """ The words said, without what a model may add around them. """
    text = (text or '').strip()
    text = re.sub(r'^(?:transcription|transcript)\s*:\s*', '', text, flags=re.IGNORECASE)
    if len(text) > 1 and text[0] in '"\'“' and text[-1] in '"\'”':
        text = text[1:-1]
    return text.strip()
