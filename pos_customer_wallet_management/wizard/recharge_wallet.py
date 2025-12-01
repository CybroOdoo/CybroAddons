# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.exceptions import ValidationError


class RechargeWallet(models.TransientModel):
    """Wallet recharge fields"""
    _name = "recharge.wallet"
    _description = "Create Wallet Recharge Of Each Customer"

    journal_id = fields.Many2one("account.journal", string="Payment Journal",
                                 help="Select journal type")
    recharge_amount = fields.Float(string="Recharge Amount",
                                   help="Recharge amount in wallet")

    def action_submit(self):
        """Create wallet recharge and wallet transaction Raises
            ValidationError: If the recharge amount is less than or equal to zero."""
        if self.recharge_amount <= 0:
            raise ValidationError("Recharge amount must be greater than zero.")
        partner = self.env['res.partner'].browse(
            self.env.context.get('active_id'))
        partner.write({
            'wallet_balance': partner.wallet_balance + self.recharge_amount})
        current_session = self.env['pos.session'].search([('state', '=', 'opened')], limit=1)
        session_name = current_session.name if current_session else "Credit"
        self.env['wallet.transaction'].create({
            'type': "Credit",
            'customer': partner.name,
            'amount': self.recharge_amount,
            'pos_order': session_name,
            'currency': partner.currency_id.name
        })
        self.env['account.payment'].create({
            'amount': self.recharge_amount,
            'payment_type': "inbound",
            'partner_id': partner.id,
            'journal_id': self.journal_id.id
        })

    @api.model
    def frontend_recharge(self, partner_id, amount_input, currency, session_id, journal_id):
        """Create functions for frontend wallet recharge"""
        partner = self.env['res.partner'].browse(partner_id)
        session = self.env['pos.session'].browse(session_id)
        journal = self.env['account.journal'].browse(journal_id)

        if session.exists():
            session_name = session.name
        else:
            current_session = self.env['pos.session'].search([('state', '=', 'opened')], limit=1)
            session_name = current_session.name if current_session else "POS Recharge"

        self.env['wallet.transaction'].create({
            'type': "Credit",
            'customer': partner.name,
            'amount': amount_input,
            'pos_order': session_name,
            'currency': currency
        })
        self.env['account.payment'].create({
            'amount': amount_input,
            'payment_type': "inbound",
            'partner_id': partner.id,
            'journal_id': journal.id
        })

        partner.wallet_balance += int(amount_input)
