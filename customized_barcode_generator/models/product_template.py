# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """This class inherits model product.template and adds fields"""
    _inherit = 'product.template'
    cost_in_code = fields.Char(string='Cost in code',
                               compute='get_cost_in_code',
                               help="Get the cost in code.")

    @api.depends('standard_price')
    def get_cost_in_code(self):
        """This function computes the cost in code based on the cost of
        product"""
        code = self.env['barcode.code'].sudo().search(
            [('active_check', '=', True)])
        active_check = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'require_standard_price'), ('value', '=', True)])
        if active_check:
            if code:
                real = str(self.standard_price).split('.')[0]
                for i in real:
                    if i == '0':
                        real = real.replace('0', code.code_for_zero)
                    elif i == '1':
                        real = real.replace('1', code.code_for_one)
                    elif i == '2':
                        real = real.replace('2', code.code_for_two)
                    elif i == '3':
                        real = real.replace('3', code.code_for_three)
                    elif i == '4':
                        real = real.replace('4', code.code_for_four)
                    elif i == '5':
                        real = real.replace('5', code.code_for_five)
                    elif i == '6':
                        real = real.replace('6', code.code_for_six)
                    elif i == '7':
                        real = real.replace('7', code.code_for_seven)
                    elif i == '8':
                        real = real.replace('8', code.code_for_eight)
                    else:
                        real = real.replace('9', code.code_for_nine)
                return real
            else:
                return " "
        else:
            return " "

    def get_product_ref(self):
        """This function is used to compute the product reference"""
        active_check = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'require_ref'), ('value', '=', True)])
        if active_check:
            return self.default_code
        else:
            return " "
