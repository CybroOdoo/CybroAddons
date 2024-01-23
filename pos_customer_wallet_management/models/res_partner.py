# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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


class ResPartner(models.Model):
    """Add field into res partner"""
    _inherit = 'res.partner'

    wallet_balance = fields.Float(string="Wallet Balance",
                                  help="Wallet balance of each employee")
    wallet_count = fields.Integer(string="Wallet",
                                  compute='_compute_wallet_count',
                                  help="Count of each wallet recharge")

    def action_recharge(self):
        """Open wizard for wallet recharge"""
        return {
            'name': 'Wallet Recharge',
            'type': 'ir.actions.act_window',
            'res_model': 'recharge.wallet',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }

    def action_number_of_wallet(self):
        """Wallet balance tree view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Wallet',
            'view_mode': 'tree',
            'res_model': 'wallet.transaction',
            'domain': [('customer', '=', self.name)],
            'context': "{'create': False}"
        }

    def _compute_wallet_count(self):
        """Count of wallet balance"""
        for record in self:
            record.wallet_count = self.env['wallet.transaction'].search_count(
                [('customer', '=', self.name)])

    @api.model
    def write_value(self, balance, order, session, price, currency_id):
        """Write remaining balance into customer wallet balance"""
        self.env['res.partner'].browse(order['id']).write({
            'wallet_balance': balance
        })
        self.env['wallet.transaction'].create({
            'type': "Debit",
            'customer': order['name'],
            'amount': price,
            'pos_order': session,
            'currency': currency_id,
        })
