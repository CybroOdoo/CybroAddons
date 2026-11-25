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
import asyncio
import concurrent.futures
import inspect
from googletrans import Translator
from odoo import api, fields, models


class OraLanguage(models.Model):
    """Managing supported languages for the AI voice assistant."""
    _name = "ora.language"
    _description = "Ora Language"

    name = fields.Char(help="The display name of the language"
                            " (e.g., English, Spanish).")
    code = fields.Char(help="The ISO language code used for "
                            "translation (e.g., 'en', 'es').")
    first_msg = fields.Char(string='First Message',
                            help="The default welcome message that"
                                 " the assistant will say in this language.")
    voice = fields.Char(help="The identifier of the voice profile used "
                             "for text-to-speech in this language.")

    def _translate_text(self, text, target_lang):
        """Translates the given text into the specified
        language using Googletrans."""
        if not text:
            return ""
        translator = Translator()
        translated = translator.translate(text, dest=target_lang)
        if inspect.iscoroutine(translated):
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    translated = pool.submit(asyncio.run, translated).result()
            else:
                translated = asyncio.run(translated)
        return translated.text if hasattr(translated, 'text') else str(translated)

    @api.model
    def get_language(self, language):
        """ Retrieves assistant language settings and translated content."""
        if language:
            rec = self.search([('code', '=', language)])
            assistant = self.env['ora.ai'].search(
                [('is_lang_switch', '=', True)], limit=1)
            prompt = assistant.prompt or ""
            target_str = "The sales order for customer [Customer Name] has been successfully created. Goodbye!"
            if target_str in prompt:
                prompt = prompt.replace(
                    target_str,
                    self._translate_text("The sales order has been created. Goodbye!", language))
            elif "say thankyou for ordering and goodbye" in prompt:
                prompt = prompt.replace(
                    "say thankyou for ordering and goodbye",
                    self._translate_text("The sales order has been created. Goodbye!", language))
            return {"first_msg": rec.first_msg,
                    "voice": rec.voice,
                    "assistant_prompt": prompt,
                    "end_msg": self._translate_text(
                        f"{assistant.end_call_phrases}", language),
                    "status": True}
        else:
            return {"status": False}
