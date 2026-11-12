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

import os
import shutil
import tempfile

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..tools import cloud_whisper, stt_client

# Where Save Subtitle Debug Audio keeps the received utterances (shared with the controller)
DEBUG_AUDIO_DIR = os.path.join(tempfile.gettempdir(), "odoo_subtitle_debug")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    meeting_stt_engine = fields.Selection(
        [
            ('whisper', 'Whisper'),
            ('whistle', 'Whistle'),
            ('grok', 'Grok STT'),
            ('cloud_whisper', 'Cloud Whisper'),
        ],
        string='Speech-to-Text Engine',
        default='whisper',
        config_parameter='meeting_transcription_summary.stt_engine',
        help='Whisper: the most accurate local engine, 99 languages. '
             'Whistle: a tiny, fast local engine for English, German, French, Spanish, Italian, Dutch and '
             'Polish only. '
             'Grok STT: xAI cloud transcription, most accurate, with no load on this server. '
             'Cloud Whisper: Whisper behind an OpenAI-compatible API (Groq, OpenAI or your own GPU server).',
    )
    meeting_xai_api_key = fields.Char(
        string='xAI API Key',
        config_parameter='meeting_transcription_summary.xai_api_key',
        help='Key of the xAI account used by Grok STT. Meeting audio is sent to xAI to be transcribed.',
    )
    meeting_cloud_whisper_url = fields.Char(
        string='Cloud Whisper URL',
        default=cloud_whisper.DEFAULT_URL,
        config_parameter='meeting_transcription_summary.cloud_whisper_url',
        help='Base URL of the OpenAI-compatible API, without /audio/transcriptions: '
             'https://api.groq.com/openai/v1 (Groq), https://api.openai.com/v1 (OpenAI), '
             'or the address of your own Whisper server.',
    )
    meeting_cloud_whisper_model = fields.Char(
        string='Cloud Whisper Model',
        default=cloud_whisper.DEFAULT_MODEL,
        config_parameter='meeting_transcription_summary.cloud_whisper_model',
        help='Whisper model name at that provider, e.g. whisper-large-v3 (Groq) or whisper-1 (OpenAI).',
    )
    meeting_cloud_whisper_api_key = fields.Char(
        string='Cloud Whisper API Key',
        config_parameter='meeting_transcription_summary.cloud_whisper_api_key',
        help='Key of the account at that provider; leave empty for a server of your own that needs none. '
             'Meeting audio is sent to that address to be transcribed.',
    )
    meeting_subtitles_keywords = fields.Char(
        string='Subtitle Keywords',
        config_parameter='meeting_transcription_summary.keywords',
        help='Comma-separated names and terms to recognize correctly (e.g. Odoo, Cybrosys). '
             'Participant names are added automatically.',
    )
    meeting_stt_openai_fallback = fields.Boolean(
        string='OpenAI Speech Fallback',
        config_parameter='meeting_transcription_summary.stt_openai_fallback',
        help='When the local speech engine fails on a live caption or an uploaded recording (error, busy, '
             'not installed), send that audio to the OpenAI Whisper API instead, with the OpenAI API Key. '
             'Meeting audio then leaves this server.',
    )
    meeting_save_debug_audio = fields.Boolean(
        string='Save Subtitle Debug Audio',
        config_parameter='meeting_transcription_summary.save_debug_audio',
        help='Keep the last 50 received utterances as WAV files in the server temp folder (odoo_subtitle_debug) '
             'to diagnose recognition problems. Disable in production: it stores meeting audio. '
             'Turning it off deletes the saved files.',
    )
    meeting_whisper_model = fields.Selection(
        [
            ('tiny', 'Tiny'),
            ('base', 'Base'),
            ('small', 'Small'),
            ('medium', 'Medium'),
            ('distil-large-v3', 'Distil Large v3'),
            ('large-v3', 'Large v3'),
        ],
        string='Whisper Model',
        default='small',
        config_parameter='meeting_transcription_summary.whisper_model',
        help='Local speech-to-text model. Bigger models are far more accurate but slower. Downloaded on first use. '
             'Tiny: fastest, least accurate. Base: fast, basic accuracy. Small: the recommended balance. '
             'Medium: accurate, needs a strong CPU or a GPU. Distil Large v3: very accurate, English only. '
             'Large v3: best accuracy, needs a GPU.',
    )
    meeting_stt_workers = fields.Integer(
        string='Speech Workers',
        default=1,
        config_parameter='meeting_transcription_summary.stt_workers',
        help='How many captions Whisper transcribes at the same time (1 to 4), so people speaking at once '
             'don\'t wait for each other. Only raise it on a server with CPU cores to spare: otherwise the '
             'captions share the same cores and each one takes longer. Each worker needs a little more '
             'memory. The text is the same either way.',
    )
    meeting_ai_provider = fields.Selection(
        [
            ('internal', 'Built-in Smart Summarizer'),
            ('openai', 'OpenAI'),
            ('ollama', 'Ollama / Local Engine'),
        ],
        string='Meeting AI Provider',
        default='internal',
        config_parameter='meeting_transcription_summary.ai_provider',
        help='Engine used to summarize meeting transcripts. '
             'Built-in Smart Summarizer: needs no API key. OpenAI: ChatGPT models. '
             'Ollama / Local Engine: a model on your own server, such as Needle or Llama 3.',
    )
    meeting_openai_api_key = fields.Char(
        string='OpenAI API Key',
        config_parameter='meeting_transcription_summary.openai_api_key',
    )
    meeting_openai_model = fields.Char(
        string='OpenAI Model',
        default='gpt-4o-mini',
        config_parameter='meeting_transcription_summary.openai_model',
    )
    meeting_ollama_endpoint = fields.Char(
        string='Ollama Endpoint URL',
        default='http://localhost:11434',
        config_parameter='meeting_transcription_summary.ollama_endpoint',
    )
    meeting_ollama_model = fields.Char(
        string='Ollama Model',
        default='llama3',
        config_parameter='meeting_transcription_summary.ollama_model',
    )
    meeting_main_language = fields.Selection(
        lambda self: [option for option in self._fields['meeting_subtitles_default_language'].selection if option[0] != 'auto'],
        string='Main Meeting Language',
        default='en-US',
        config_parameter='meeting_transcription_summary.main_language',
        help='With auto-detect, this language is assumed whenever the detection is unsure, so short or '
             'accented phrases are not mistaken for another language. Other languages are still recognized '
             'when clearly spoken.',
    )
    meeting_subtitles_default_language = fields.Selection(
        [
            ('auto', 'Auto-Detect'),
            ('en-US', 'US English'),
            ('en-GB', 'UK English'),
            ('es-ES', 'Spanish'),
            ('fr-FR', 'French'),
            ('de-DE', 'German'),
            ('it-IT', 'Italian'),
            ('nl-NL', 'Dutch'),
            ('pl-PL', 'Polish'),
            ('pt-PT', 'Portuguese'),
            ('hi-IN', 'Hindi'),
            ('ml-IN', 'Malayalam'),
            ('ta-IN', 'Tamil'),
            ('ar-SA', 'Arabic'),
        ],
        string='Subtitles Speech Language',
        default='en-US',
        config_parameter='meeting_transcription_summary.subtitles_language',
        help='The language people speak in meetings. Auto-Detect is less accurate on short phrases.',
    )

    meeting_stt_missing_package = fields.Char(
        string='Missing Speech Package',
        compute='_compute_meeting_stt_missing_package',
        help='What the selected engine needs that is not installed on this server.',
    )

    @api.depends('meeting_stt_engine')
    def _compute_meeting_stt_missing_package(self):
        for settings in self:
            engine = settings.meeting_stt_engine
            message = False
            if engine in ('whisper', 'whistle'):
                package = stt_client.missing_package(engine)
                if package:
                    message = self.env._(
                        "This engine needs the %(package)s Python package, which is not installed on this "
                        "server: captions stay empty until it is. Install it in the Python environment that "
                        "runs Odoo (pip install %(package)s), then restart Odoo.",
                        package=package)
            elif engine == 'cloud_whisper' and stt_client.missing_package('whisper'):
                message = self.env._(
                    "Live captions work without it, but uploaded recordings are transcribed by the local "
                    "Whisper model, which needs the faster-whisper Python package: install it in the Python "
                    "environment that runs Odoo (pip install faster-whisper), then restart Odoo.")
            settings.meeting_stt_missing_package = message

    @api.constrains('meeting_stt_workers')
    def _check_meeting_stt_workers(self):
        for settings in self:
            if not 1 <= settings.meeting_stt_workers <= 4:
                raise ValidationError(self.env._("Speech Workers must be between 1 and 4."))

    def set_values(self):
        was_saving = self.env['ir.config_parameter'].sudo().get_param(
            'meeting_transcription_summary.save_debug_audio') in ('True', '1')
        res = super().set_values()
        if was_saving and not self.meeting_save_debug_audio:
            # it holds meeting audio: none of it stays behind once debugging is over
            shutil.rmtree(DEBUG_AUDIO_DIR, ignore_errors=True)
        return res
