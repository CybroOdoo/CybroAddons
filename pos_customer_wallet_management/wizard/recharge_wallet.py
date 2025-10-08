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


class RechargeWallet(models.TransientModel):
    """Wallet recharge fields"""
    _name = "recharge.wallet"
    _description = "Create Wallet Recharge Of Each Customer"

    journal_id = fields.Many2one("account.journal", string="Payment Journal",
                                 help="Select journal type")
    recharge_amount = fields.Float(string="Recharge Amount",
                                   help="Recharge amount in wallet")

    def action_submit(self):
        """Create wallet recharge and wallet transaction"""
        partner = self.env['res.partner'].browse(
            self.env.context.get('active_id'))
        partner.write({
            'wallet_balance': partner.wallet_balance + self.recharge_amount})
        self.env['wallet.transaction'].create({
            'type': "Credit",
            'customer': partner.name,
            'amount': self.recharge_amount,
            'currency': partner.currency_id.name
        })
        self.env['account.payment'].create({
            'amount': self.recharge_amount,
            'ref': "Wallet Recharge",
            'payment_type': "inbound",
            'partner_id': partner.id
        })

    @api.model
    def frontend_recharge(self, partner, amount_input, currency):
        """Create functions for frontend wallet recharge"""
        self.env['wallet.transaction'].create({
            'type': "Credit",
            'customer': partner['name'],
            'amount': amount_input,
            'currency': currency
        })
        self.env['account.payment'].create({
            'amount': amount_input,
            'ref': "Wallet Recharge",
            'payment_type': "inbound",
            'partner_id': partner['id']
        })
        self.env['res.partner'].browse(partner['id']).write({
            'wallet_balance': partner['wallet_balance'] + int(amount_input)
        })
