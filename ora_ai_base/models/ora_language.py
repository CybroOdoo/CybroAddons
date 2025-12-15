# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from googletrans import Translator
from odoo import api, fields, models


class OraLanguage(models.Model):
    """Managing supported languages for the AI voice assistant."""
    _name = "ora.language"
    _description = "Ora Language"

    name = fields.Char(string='Name',
                       help="The display name of the language"
                            " (e.g., English, Spanish).")
    code = fields.Char(string='Code',
                       help="The ISO language code used for "
                            "translation (e.g., 'en', 'es').")
    first_msg = fields.Char(string='First Message',
                            help="The default welcome message that"
                                 " the assistant will say in this language.")
    voice = fields.Char(string='Voice',
                        help="The identifier of the voice profile used "
                             "for text-to-speech in this language.")

    def _translate_text(self, text, target_lang):
        """Translates the given text into the specified
        language using Googletrans."""
        translator = Translator()
        translated = translator.translate(text, dest=target_lang)
        return translated.text

    @api.model
    def get_language(self, language):
        """ Retrieves assistant language settings and translated content."""
        if language:
            rec = self.search([('code', '=', language)])
            assistant = self.env['ora.ai'].search(
                [('is_lang_switch', '=', True)], limit=1)
            prompt = assistant.prompt.replace(
                "say thankyou for ordering and goodbye",
                self._translate_text("say thankyou for "
                                     "ordering and goodbye", language))
            return {"first_msg": rec.first_msg,
                    "voice": rec.voice,
                    "assistant_prompt": prompt,
                    "end_msg": self._translate_text(
                        f"{assistant.end_call_phrases}", language),
                    "status": True}
        else:
            return {"status": False}
