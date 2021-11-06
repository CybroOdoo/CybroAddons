# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: LINTO C T(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
try:
    from googletrans import Translator
    translator = Translator()
except ImportError:
    print "Unable to import "

from odoo import models, fields, _
from odoo.exceptions import UserError


class LanguageList(models.Model):
    _name = 'languages.list'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")


class TranslationHelper(models.Model):
    _inherit = 'ir.translation'

    def translate_term(self):
        if self.lang:
            lang = dict(self.fields_get(allfields=['lang'])['lang']['selection'])[self.lang]
            rec = self.env['languages.list'].search([('name', '=', lang)], limit=1)
            if rec:
                code = rec.code
            if self.source and code:
                try:
                    val = translator.translate(self.source, dest=code)
                    time.sleep(1)
                    self.value = val.text
                except:
                    raise UserError(_("No Translation Found. Please Check Your Internet Connection."))
            else:
                raise UserError(_("There is nothing to translate !"))
        else:
            raise UserError(_("Select a language!"))
