# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Athul Raj B S (odoo@cybrosys.info)
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
from odoo import models, fields, api


class AccountPaymentRegister(models.TransientModel):
    """
    Model to inherit 'account.payment.register' for handling POS partial payment
    registration and syncing POS order state and payment records.
    """
    _inherit = 'account.payment.register'

    is_pos_order = fields.Boolean(
        string='Is POS Order',
        help='Indicates whether this account move is associated with a POS order.',
        compute='_compute_is_pos_order',
    )

    pos_payment_method_id = fields.Many2one(
        comodel_name='pos.payment.method',
        string='POS Payment Method',
        help='The payment method used for the POS order.',
    )

    @api.depends('amount', 'line_ids')
    def _compute_is_pos_order(self):
        """
        Compute 'is_pos_order' field to determine if the account move being paid
        is associated with an invoiced partially paid POS order.
        """
        for record in self:
            invoice_ids = record.line_ids.move_id.ids or self._context.get('active_ids', [])
            pos_order = self.env['pos.order'].search([
                ('account_move', 'in', invoice_ids),
                ('state', '=', 'invoiced'),
                ('is_partial_payment', '=', True)
            ], limit=1)
            record.is_pos_order = bool(pos_order)

    def action_create_payments(self):
        """
        Override 'action_create_payments' method to create pos.payment line
        and update POS order paid amount and state upon invoice payment creation.
        """
        res = super(AccountPaymentRegister, self).action_create_payments()
        invoice_ids = self.line_ids.move_id.ids or self._context.get('active_ids', [])

        pos_orders = self.env['pos.order'].search([
            ('account_move', 'in', invoice_ids),
            ('state', '=', 'invoiced'),
            ('is_partial_payment', '=', True)
        ])

        for pos_order in pos_orders:
            # Determine payment amount allocated to this POS order's invoice
            order_lines = self.line_ids.filtered(lambda l: l.move_id == pos_order.account_move)
            if order_lines and len(self.line_ids.move_id) > 1:
                allocated_amount = sum(abs(l.amount_residual) for l in order_lines)
                payment_amount = min(allocated_amount, self.amount) if allocated_amount else (self.amount / len(pos_orders))
            else:
                payment_amount = self.amount

            if self.pos_payment_method_id and payment_amount > 0:
                payment_date = fields.Datetime.to_datetime(self.payment_date) if self.payment_date else fields.Datetime.now()
                self.env['pos.payment'].create({
                    'pos_order_id': pos_order.id,
                    'amount': payment_amount,
                    'payment_method_id': self.pos_payment_method_id.id,
                    'payment_date': payment_date,
                    'session_id': pos_order.session_id.id,
                })
                pos_order.write({
                    'amount_paid': pos_order.amount_paid + payment_amount,
                })
            if pos_order.amount_paid >= pos_order.amount_total:
                pos_order.write({
                    'state': 'paid',
                    'is_partial_payment': False,
                })
        return res
