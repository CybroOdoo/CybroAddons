# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):  # pylint: disable=too-few-public-methods
    """Add extra fields to the settings."""
    _inherit = 'res.config.settings'

    hide_price = fields.Boolean(
        config_parameter='website_hide_button.hide_price',
        help="If enabled, the price of the product will not be visible "
             "to guest users on the website.")
    hide_cart = fields.Boolean(
        config_parameter='website_hide_button.hide_cart',
        help="If enabled, the Add to Cart button and cart icon will be "
             "hidden from guest users.")

    @api.model
    def get_smartsupp_details(self):
        """Return the stored hide price / hide cart values."""
        params = self.env['ir.config_parameter'].sudo()
        return {
            'hide_price': params.get_str('website_hide_button.hide_price'),
            'hide_cart': params.get_str('website_hide_button.hide_cart'),
        }

    @api.onchange('hide_price')
    def _onchange_hide_price(self):
        """Hiding the price also hides the cart."""
        if self.hide_price:
            self.hide_cart = True
