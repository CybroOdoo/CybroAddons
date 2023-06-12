# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana J(<https://www.cybrosys.com>)
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
#############################################################################
"""pos session"""
from odoo import fields, models, Command, _
from odoo.tools import float_compare


class PosSession(models.Model):
    """inherit pos session to add branch field"""
    _inherit = 'pos.session'

    branch_id = fields.Many2one('res.branch', related='config_id.branch_id',
                                string="Branch", help='Allowed Branches',
                                readonly=True)

    def _create_account_move(self, balancing_account=False, amount_to_balance=0,
                             bank_payment_method_diffs=None):
        """ Create account.move and account.move.line records for this session.

        Side-effects include:
            - setting self.move_id to the created account.move record
            - creating and validating account.bank.statement for cash payments
            - reconciling cash receivable lines, invoice receivable lines and
            stock output lines
        """
        journal = self.config_id.journal_id
        # Passing default_journal_id for the calculation of default currency
        # of account move
        # See _get_default_currency in the account/account_move.py.
        account_move = self.env['account.move'].with_context(
            default_journal_id=journal.id).create({
                'journal_id': journal.id,
                'date': fields.Date.context_today(self),
                'ref': self.name,
                'branch_id': self.branch_id.id
            })
        self.write({'move_id': account_move.id})

        data = {'bank_payment_method_diffs': bank_payment_method_diffs or {}}
        data = self._accumulate_amounts(data)
        data = self._create_non_reconciliable_move_lines(data)
        data = self._create_bank_payment_moves(data)
        data = self._create_pay_later_receivable_lines(data)
        data = self._create_cash_statement_lines_and_cash_move_lines(data)
        data = self._create_invoice_receivable_lines(data)
        data = self._create_stock_output_lines(data)
        if balancing_account and amount_to_balance:
            data = self._create_balancing_line(data, balancing_account,
                                               amount_to_balance)
        return data

    def _create_split_account_payment(self, payment, amounts):
        """creating split of account payments"""
        payment_method = payment.payment_method_id
        if not payment_method.journal_id:
            return self.env['account.move.line']
        outstanding_account = \
            payment_method.outstanding_account_id or \
            self.company_id.account_journal_payment_debit_account_id
        account_payment = self.env['account.payment'].create({
            'amount': amounts['amount'],
            'partner_id': payment.partner_id.id,
            'journal_id': payment_method.journal_id.id,
            'force_outstanding_account_id': outstanding_account.id,
            'ref': _('%s POS payment of %s in %s') % (payment_method.name,
                                                      payment.partner_id
                                                      .display_name, self.name),
            'pos_payment_method_id': payment_method.id,
            'pos_session_id': self.id,
            'branch_id': self.branch_id.id
        })
        account_payment.action_post()
        return account_payment.move_id.line_ids.filtered(
            lambda line: line.account_id ==
                         account_payment.destination_account_id)

    def _create_combine_account_payment(self, payment_method, amounts,
                                        diff_amount):
        """creating combined account payment"""
        outstanding_account = \
            payment_method.outstanding_account_id or \
            self.company_id.account_journal_payment_debit_account_id
        destination_account = self._get_receivable_account(payment_method)

        if float_compare(amounts['amount'], 0,
                         precision_rounding=self.currency_id.rounding) < 0:
            # revert the accounts because account.payment doesn't
            # accept negative amount.
            outstanding_account, destination_account = destination_account, \
                outstanding_account

        account_payment = self.env['account.payment'].create({
            'amount': abs(amounts['amount']),
            'journal_id': payment_method.journal_id.id,
            'force_outstanding_account_id': outstanding_account.id,
            'destination_account_id':  destination_account.id,
            'ref': _('Combine %s POS payments from %s') % (payment_method.name,
                                                           self.name),
            'pos_payment_method_id': payment_method.id,
            'pos_session_id': self.id,
            'branch_id': self.branch_id.id
        })
        diff_amount_compare_to_zero = \
            self.currency_id.compare_amounts(diff_amount, 0)
        if diff_amount_compare_to_zero != 0:
            self._apply_diff_on_account_payment_move(account_payment,
                                                     payment_method,
                                                     diff_amount)
        account_payment.action_post()
        return account_payment.move_id.line_ids\
            .filtered(lambda line: line.account_id == account_payment.
                      destination_account_id)

    def _create_diff_account_move_for_split_payment_method(self,
                                                           payment_method,
                                                           diff_amount):
        """ Creating different account moves for split payment method"""
        self.ensure_one()

        get_diff_vals_result = self._get_diff_vals(payment_method.id,
                                                   diff_amount)
        if not get_diff_vals_result:
            return

        source_vals, dest_vals = get_diff_vals_result
        diff_move = self.env['account.move'].create({
            'journal_id': payment_method.journal_id.id,
            'date': fields.Date.context_today(self),
            'ref': self._get_diff_account_move_ref(payment_method),
            'line_ids': [Command.create(source_vals),
                         Command.create(dest_vals)],
            'branch_id': self.branch_id.id
        })
        diff_move._post()
