# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields


class AccessRightsUsers(models.Model):
    """ Adding fields in to res users """
    _inherit = "res.users"

    disable_customer_selection = fields.Boolean(string="Disable Customer Selection", default=False)
    disable_payment_button = fields.Boolean("Disable Payment Button", default=False)
    hide_delete_button = fields.Boolean("Hide Delete Button", default=False)
    disable_price_button = fields.Boolean("Disable Price Button", default=False)
    disable_discount_button = fields.Boolean("Disable Discount Button", default=False)
    disable_plus_minus_button = fields.Boolean("Disable Plus Minus Button", default=False)
    disable_numpad = fields.Boolean("Disable Numpad", default=False)
    hide_new_orders = fields.Boolean("Hide New Orders", default=False)
    disable_remove_button = fields.Boolean("Disable Remove Button", default=False)


class PosSession(models.Model):
    """Load fields into pos session."""
    _inherit = "pos.session"

    def _pos_ui_models_to_load(self):
        """Load res.users model into pos session"""
        result = super()._pos_ui_models_to_load()
        result += [
            'res.users',
        ]
        return result

    def _loader_params_res_users(self):
        """load product.product parameters"""
        result = super()._loader_params_res_users()
        result['search_params']['fields'].extend(
            ['disable_customer_selection', 'disable_payment_button', 'hide_delete_button',
             'disable_price_button', 'disable_discount_button', 'disable_plus_minus_button',
             'disable_numpad',
             'hide_new_orders', 'disable_remove_button'])
        return result