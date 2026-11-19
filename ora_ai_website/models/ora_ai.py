# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

# Transcriber and voice used when a visitor switches the language, as before
LANGUAGE_TRANSCRIBER = {'provider': 'deepgram', 'model': 'nova-2'}
LANGUAGE_VOICE_PROVIDER = '11labs'


class OraAi(models.Model):
    """Voice assistant of the shop page"""
    _inherit = 'ora.ai'

    @api.model
    def _get_website_assistant(self):
        """Return the assistant chosen in the website settings, if it is
        enabled and created on Vapi"""
        params = self.env['ir.config_parameter'].sudo()
        if not params.get_bool('ora_ai_website.is_website_assistant'):
            return self.browse()
        assistant = self.sudo().browse(
            params.get_int('ora_ai_website.website_assistant_id')).exists()
        return assistant.filtered(
            lambda rec: rec.state == 'done' and rec.id_assistant)

    def _get_language_overrides(self, code):
        """Settings of the call in the language the visitor chose, sent by
        the browser when the call starts again. The assistant on Vapi is
        not changed, so other visitors keep their own language."""
        self.ensure_one()
        language = self.language_ids.filtered(
            lambda lang: lang.code == code)[:1]
        if not self.is_lang_switch or not language:
            return {}
        end_phrase = self.end_call_phrases or ''
        # The translation service is online and may be unavailable
        try:
            end_phrase = language._translate_text(end_phrase, code)
        except Exception:  # pylint: disable=broad-exception-caught
            _logger.warning('Could not translate the end call phrase to %s',
                            code, exc_info=True)
        overrides = {
            'transcriber': {**LANGUAGE_TRANSCRIBER, 'language': code},
            'voice': {'provider': LANGUAGE_VOICE_PROVIDER,
                      'voiceId': language.voice},
            'firstMessage': language.first_msg,
        }
        if end_phrase:
            overrides['endCallPhrases'] = [end_phrase]
        return overrides
