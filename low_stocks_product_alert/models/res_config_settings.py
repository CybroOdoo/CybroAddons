# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models


class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    is_low_stock_alert = fields.Boolean(string="Low Stock Alert")
    min_low_stock_alert = fields.Integer(
        string='Alert Quantity', default=0,
        help='Change the background color for the product based'
             ' on the Alert Quant.')

    def set_values(self):
        super(ResConfig, self).set_values()

        self.env['ir.config_parameter'].set_param(
            'low_stocks_product_alert.is_low_stock_alert', self.is_low_stock_alert)

        self.env['ir.config_parameter'].set_param(
            'low_stocks_product_alert.min_low_stock_alert', self.min_low_stock_alert)

    @api.model
    def get_values(self):
        res = super(ResConfig, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            is_low_stock_alert=params.get_param(
                'low_stocks_product_alert.is_low_stock_alert'),
            min_low_stock_alert=params.get_param(
                'low_stocks_product_alert.min_low_stock_alert'),
        )
        return res
