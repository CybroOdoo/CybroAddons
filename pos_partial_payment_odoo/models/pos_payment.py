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
from odoo import models, fields
from odoo.tools import float_is_zero, _

class PosPayment(models.Model):
    """
    This class extends the 'pos.payment' model and overrides the
    '_create_payment_moves' method to customize how accounting moves are
    created for payments in the Point of Sale system.
    """
    _inherit = 'pos.payment'

    def _create_payment_moves(self, is_reverse=False):
        """Custom version of _create_payment_moves
        Modified condition for handling change payments.
        """
        result = self.env['account.move']
        credit_line_ids = []

        # Define payments
        change_payment = self.filtered(lambda p: p.is_change and p.payment_method_id.type == 'cash')
        payment_to_change = self.filtered(lambda p: not p.is_change and p.payment_method_id.type == 'cash')[:1]

        # Iterate through payments excluding change payments
        for payment in self - change_payment:
            order = payment.pos_order_id
            payment_method = payment.payment_method_id

            # Skip pay_later or zero amounts
            if payment_method.type == 'pay_later' or float_is_zero(payment.amount, precision_rounding=order.currency_id.rounding):
                continue

            accounting_partner = self.env["res.partner"]._find_accounting_partner(payment.partner_id)
            pos_session = order.session_id
            journal = pos_session.config_id.journal_id

            # ✅ Your modified condition here
            if change_payment or payment == payment_to_change:
                pos_payment_ids = payment.ids + change_payment.ids
                payment_amount = payment.amount
            else:
                pos_payment_ids = payment.ids
                payment_amount = payment.amount

            # Create the accounting move for the payment
            payment_move = self.env['account.move'].with_context(default_journal_id=journal.id).create({
                'journal_id': journal.id,
                'date': fields.Date.context_today(order, order.date_order),
                'ref': _('Invoice payment for %(order)s (%(account_move)s) using %(payment_method)s',
                         order=order.name,
                         account_move=order.account_move.name,
                         payment_method=payment_method.name),
                'pos_payment_ids': pos_payment_ids,
            })
            result |= payment_move

            # Link payment with its move
            payment.write({'account_move_id': payment_move.id})

            # Compute amounts
            amounts = pos_session._update_amounts({'amount': 0, 'amount_converted': 0},
                                                  {'amount': payment_amount}, payment.payment_date)

            # Create credit line
            credit_line_vals = pos_session._credit_amounts({
                'account_id': accounting_partner.with_company(order.company_id).property_account_receivable_id.id,
                'partner_id': accounting_partner.id,
                'move_id': payment_move.id,
            }, amounts['amount'], amounts['amount_converted'])

            # Handle debit line
            is_split_transaction = payment.payment_method_id.split_transactions
            if is_split_transaction and is_reverse:
                reversed_move_receivable_account_id = accounting_partner.with_company(order.company_id).property_account_receivable_id.id
            elif is_reverse:
                reversed_move_receivable_account_id = payment.payment_method_id.receivable_account_id.id or self.company_id.account_default_pos_receivable_account_id.id
            else:
                reversed_move_receivable_account_id = self.company_id.account_default_pos_receivable_account_id.id

            debit_line_vals = pos_session._debit_amounts({
                'account_id': reversed_move_receivable_account_id,
                'move_id': payment_move.id,
                'partner_id': accounting_partner.id if is_split_transaction and is_reverse else False,
            }, amounts['amount'], amounts['amount_converted'])

            # Create move lines
            lines = self.env['account.move.line'].create([credit_line_vals, debit_line_vals])

            # Store credit/debit line IDs
            if amounts['amount_converted'] < 0:
                credit_line_ids += lines.filtered(lambda l: l.debit).ids
            else:
                credit_line_ids += lines.filtered(lambda l: l.credit).ids

            # Post the move
            payment_move._post()

        return result.with_context(credit_line_ids=credit_line_ids)
