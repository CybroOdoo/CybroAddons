# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from googletrans import Translator
from odoo import api, models


class TranslationHelper(models.Model):
    """ Class to create translation for selected words"""
    _name = 'translation.helper'
    _description = 'Translation Helper'

    @api.model
    def translate_term(self, args, target_languages):
        """Function to translate the terms"""
        translations = {}
        for target_language in target_languages:
            translator = Translator()
            # Translate the term to the current target language
            translated_text = ''
            try:
                translated_text = translator.translate(args,
                                                   dest=target_language).text
            except Exception:
                pass
            translations[target_language] = translated_text
        return translations
