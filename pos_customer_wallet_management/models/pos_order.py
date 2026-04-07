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
from odoo import fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    is_wallet_deducted = fields.Boolean(string="Is Wallet Deducted", default=False, copy=False)

    def _deduct_wallet_amount(self):
        """
        Backend fallback: only deduct if frontend did NOT already do it via write_value.
        The frontend sets is_wallet_deducted=True via write_value's transaction creation.
        We rely on is_wallet_deducted to prevent double deduction.
        """
        for order in self:
            if order.is_wallet_deducted or not order.partner_id:
                continue
            wallet_lines = order.payment_ids.filtered(
                lambda p: p.payment_method_id.is_wallet_journal and p.amount > 0 and not p.is_change
            )
            wallet_amount = sum(wallet_lines.mapped("amount"))
            if not wallet_amount:
                continue

            # Check if the frontend already created a Debit transaction for this order.
            # Frontend uses the UUID as order ref. Match by partner + amount + Debit type.
            existing = self.env['wallet.transaction'].sudo().search([
                ('customer', '=', order.partner_id.name),
                ('amount', '=', wallet_amount),
                ('type', '=', 'Debit'),
            ], limit=1)
            if existing:
                # Frontend already handled it — just mark the flag and skip
                order.is_wallet_deducted = True
                continue

            if order.partner_id.wallet_balance < wallet_amount:
                continue

            order.partner_id.sudo().write({
                'wallet_balance': order.partner_id.wallet_balance - wallet_amount
            })
            pos_ref = order.pos_reference or order.name or f"Order-{order.id}"
            self.env["wallet.transaction"].sudo().create({
                "type": "Debit",
                "customer": order.partner_id.name,
                "amount": wallet_amount,
                "pos_order": pos_ref,
                "currency": order.currency_id.name,
            })
            order.is_wallet_deducted = True

    def action_pos_order_paid(self):
        res = super().action_pos_order_paid()
        self._deduct_wallet_amount()
        return res
