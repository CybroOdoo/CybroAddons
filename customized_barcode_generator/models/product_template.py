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


class ProductTemplate(models.Model):
    """ This class inherits model product.template and adds field for code """
    _inherit = 'product.template'

    cost_in_code = fields.Char(string='Cost in Code',
                               compute='_compute_cost_in_code',
                               help="Cost of the product encoded with the "
                                    "active barcode code rule.")

    @api.depends('standard_price')
    def _compute_cost_in_code(self):
        """ This function computes the cost in code based on the cost of
        product """
        code = self.env['barcode.code'].sudo().search(
            [('active_check', '=', True)], limit=1)
        active_check = self.env['ir.config_parameter'].sudo().get_bool(
            'customized_barcode_generator.require_standard_price')
        for record in self:
            if active_check and code:
                digit_map = {
                    '0': code.code_for_zero,
                    '1': code.code_for_one,
                    '2': code.code_for_two,
                    '3': code.code_for_three,
                    '4': code.code_for_four,
                    '5': code.code_for_five,
                    '6': code.code_for_six,
                    '7': code.code_for_seven,
                    '8': code.code_for_eight,
                    '9': code.code_for_nine,
                }
                real = str(int(record.standard_price))
                record.cost_in_code = ''.join(
                    digit_map.get(ch, ch) for ch in real)
            else:
                record.cost_in_code = False
