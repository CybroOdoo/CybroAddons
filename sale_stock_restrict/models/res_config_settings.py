# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Class to add fields and functions in settings"""
    _inherit = 'res.config.settings'

    product_restriction = fields.Boolean(
        string='Out Of Stock Product Restriction',
        help='Enable this to restrict the out of stock product')
    check_stock = fields.Selection(
        [('on_hand_quantity', 'On Hand Quantity'),
         ('forecast_quantity', 'Forecast Quantity')], string="Based On",
        help='Choose the type of restriction')

    @api.model
    def get_values(self):
        """Function to take values from the fields"""
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo().get_param
        product_restriction = params('sale_stock_restrict.product_restriction')
        check_stock = params('sale_stock_restrict.check_stock')
        res.update(
            product_restriction=product_restriction,
            check_stock=check_stock
        )
        return res

    def set_values(self):
        """Function to set the values in the fields"""
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'sale_stock_restrict.product_restriction', self.product_restriction)
        self.env['ir.config_parameter'].sudo().set_param(
            'sale_stock_restrict.check_stock', self.check_stock)
