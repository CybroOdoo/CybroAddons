# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """
    Add extra fields in the settings.
    """
    _inherit = 'res.config.settings'

    hide_price = fields.Boolean(string='Hide Price',
                                  config_parameter='website_hide_button.hide_price',
                                  help="If enabled, the price of product will not be visible to guest users in website")
    hide_cart = fields.Boolean(string='Hide Cart',
                                config_parameter='website_hide_button.hide_cart',
                                help="If enabled, the Add to Cart button and Cart Icon will be visible to guest users")

    def set_values(self):
        """Method for setting the parameters"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'website_hide_button.hide_price', self.hide_price)
        self.env['ir.config_parameter'].sudo().set_param(
            'website_hide_button.hide_cart', self.hide_cart)

    @api.model
    def get_smartsupp_details(self):
        """Method for get value"""
        hide_price = self.env['ir.config_parameter'].sudo().get_param(
            'website_hide_button.hide_price')
        hide_cart = self.env['ir.config_parameter'].sudo().get_param(
            'website_hide_button.hide_cart')
        return {
            'hide_price': hide_price,
            'hide_cart': hide_cart,
        }

    @api.onchange('hide_price')
    def _onchange_hide_price(self):
        if self.hide_price:
            self.hide_cart = True
