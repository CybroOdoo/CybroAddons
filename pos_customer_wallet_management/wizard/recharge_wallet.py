# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    _description = "Wallet Recharge Of Each Customer"

    journal_id = fields.Many2one("account.journal", string="Payment Journal",
                                 domain="[('type', 'in', ['cash', 'bank'])]",
                                 default=lambda self: self.env.ref(
                                     'pos_customer_wallet_management.pos_wallet_journal_main',
                                     raise_if_not_found=False),
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
        """Create functions for frontend wallet recharge with robust handling"""
        # Ensure integer IDs and float amount
        try:
            p_id = int(partner_id)
            j_id = int(journal_id)
            amount = float(amount_input)
        except (ValueError, TypeError):
            return False

        # Use sudo and browse to get records
        partner = self.env['res.partner'].sudo().browse(p_id)
        journal = self.env['account.journal'].sudo().browse(j_id)
        
        if not partner.exists() or not journal.exists():
            return False

        # Robust session handling
        session_name = "POS Recharge"
        if session_id:
            try:
                s_id = int(session_id)
                session = self.env['pos.session'].sudo().browse(s_id)
                if session.exists():
                    session_name = session.name
            except (ValueError, TypeError):
                pass
        
        if session_name == "POS Recharge":
            current_session = self.env['pos.session'].sudo().search([('state', '=', 'opened')], limit=1)
            if current_session:
                session_name = current_session.name

        # 1. Update Partner Balance (Sudo write to ensure persistence)
        partner.write({'wallet_balance': partner.wallet_balance + amount})

        # 2. Create Wallet Transaction
        self.env['wallet.transaction'].sudo().create({
            'type': "Credit",
            'customer': partner.name,
            'amount': amount,
            'pos_order': session_name,
            'currency': currency or partner.currency_id.name
        })

        # 3. Create Account Payment (Inbound) - Mirroring backend wizard logic
        payment_vals = {
            'amount': amount,
            'payment_type': "inbound",
            'partner_id': partner.id,
            'journal_id': journal.id,
        }
        # Attempt to find a payment method line if available (v17+ requirement)
        if hasattr(journal, 'inbound_payment_method_line_ids'):
            method_line = journal.inbound_payment_method_line_ids[:1]
            if method_line:
                payment_vals['payment_method_line_id'] = method_line.id
        
        self.env['account.payment'].sudo().create(payment_vals)
        
        return partner.wallet_balance
