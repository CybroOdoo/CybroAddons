# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PaymentProvider(models.Model):
    """Create a new records for saferpay in payment provider """
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('saferpay', "saferpay")],
        ondelete={'saferpay': 'set default'}, required_if_provider='demo',
        help="SaferPay code"
    )
    customer = fields.Char(string='Customer ID', help="Customer ID get from "
                                                      "Signup credential")
    terminal = fields.Char(string="Terminal ID", help="Terminal Id get from "
                                                      "signup credential")
    username = fields.Char(string="Username", help="Username of Safer-pay")
    password = fields.Char(string="Password", help="Password of Safer-pay")

    @api.depends('code', 'customer', 'terminal', 'username', 'password')
    def _compute_view_configuration_fields(self):
        """ Override of payment to hide the credentials page.
        :return: None"""
        super()._compute_view_configuration_fields()
        self.filtered(lambda p: p.code == 'saferpay').show_credentials_page = \
            True

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'saferpay').update({
            'support_express_checkout': True,
            'support_manual_capture': 'partial',
            'support_refund': 'partial',
            'support_tokenization': True,
        })

    @api.constrains('state', 'code')
    def _check_provider_state(self):
        if self.filtered(lambda p: p.code == 'saferpay' and p.state not in (
                'test', 'disabled')):
            raise UserError(_("saferpay providers should never be enabled."))
