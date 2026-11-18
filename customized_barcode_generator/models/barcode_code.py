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

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BarcodeCode(models.Model):
    """ This class creates a model with needed fields """
    _name = 'barcode.code'
    _description = 'Barcode Code'

    name = fields.Char(default='Numeric Code', help="Name of the code rule.")
    code_for_zero = fields.Char(string='0', required=True, size=1,
                                default='a',
                                help="Substitute character for digit 0.")
    code_for_one = fields.Char(string='1', required=True, size=1,
                               default='b',
                               help="Substitute character for digit 1.")
    code_for_two = fields.Char(string='2', required=True, size=1,
                               default='c',
                               help="Substitute character for digit 2.")
    code_for_three = fields.Char(string='3', required=True, size=1,
                                 default='d',
                                 help="Substitute character for digit 3.")
    code_for_four = fields.Char(string='4', required=True, size=1,
                                default='e',
                                help="Substitute character for digit 4.")
    code_for_five = fields.Char(string='5', required=True, size=1,
                                default='f',
                                help="Substitute character for digit 5.")
    code_for_six = fields.Char(string='6', required=True, size=1,
                               default='g',
                               help="Substitute character for digit 6.")
    code_for_seven = fields.Char(string='7', required=True, size=1,
                                 default='h',
                                 help="Substitute character for digit 7.")
    code_for_eight = fields.Char(string='8', required=True, size=1,
                                 default='i',
                                 help="Substitute character for digit 8.")
    code_for_nine = fields.Char(string='9', required=True, size=1,
                                default='j',
                                help="Substitute character for digit 9.")
    active_check = fields.Boolean(string="Active", default=False,
                                  help="Enable to make this code rule active.")
    date_check = fields.Datetime(default=fields.Datetime.now,
                                 string="Date", help="Specify the date.")

    @api.constrains('active_check')
    def _check_single_active_rule(self):
        """ Ensure that only one code rule is active at a time """
        for record in self.filtered('active_check'):
            if self.search_count([('active_check', '=', True),
                                  ('id', '!=', record.id)], limit=1):
                raise ValidationError(self.env._(
                    "Only one rule for code can be active at a time."))
