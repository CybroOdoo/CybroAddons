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
from odoo import _, fields, models

from .report_company import get_report_branches, get_report_journal_domain


class DynamicBankReconciliation(models.AbstractModel):
    """Bank Reconciliation Statement, per bank / cash journal, as of a date:

    - bank side: balance of the bank statement lines, plus the receipts and
      payments not yet on the statement (open items of the journal's
      outstanding accounts, payments without an entry not matched yet);
    - books side: the book balance and the bank transactions not yet
      reconciled (statement lines whose counterpart is still the suspense
      account);
    - the difference shows entries booked on the bank account without a
      bank statement line.

    Reconciliation status as of today, for documents dated up to the date.
    """
    _name = 'account.dynamic.report.bank_reconciliation'
    _inherit = 'account.dynamic.report'
    _description = 'Bank Reconciliation'

    _filters = ('date', 'journals')
    _date_mode = 'single'

    def _report_title(self):
        return _("Bank Reconciliation")

    def _columns(self, options):
        return [{'name': _("Amount"), 'type': 'monetary'}]

    def _report_journal_domain(self, company):
        return get_report_journal_domain(company, [('type', 'in', ('bank', 'cash'))])

    def _bank_journals(self, options):
        journals = self.env['account.journal'].search(
            self._report_journal_domain(self.env.company))
        if options['journal_ids']:
            journals = journals.filtered(lambda j: j.id in options['journal_ids'])
        return journals

    # ------------------------------------------------------------------
    def _base_domain(self, options):
        return [('parent_state', '=', 'posted'),
                ('date', '<=', fields.Date.to_string(options['date_to'])),
                ('company_id', 'in', get_report_branches(self.env.company).ids)]

    def _statement_items(self, journal, options):
        """Bank-account lines of the journal's statement lines."""
        return self.env['account.move.line'].search(self._base_domain(options) + [
            ('account_id', '=', journal.default_account_id.id),
            ('move_id.statement_line_id.journal_id', '=', journal.id)])

    def _book_items(self, journal, options):
        """All lines of the bank account."""
        return self.env['account.move.line'].search(self._base_domain(options) + [
            ('account_id', '=', journal.default_account_id.id)])

    def _outstanding(self, journal, options, inbound):
        """Open items of the outstanding receipts / payments accounts of
        the journal, and paid payments without a journal entry that are not
        matched with a bank statement line yet."""
        # As core's payment liquidity accounts: the journal's outstanding
        # accounts and the outstanding account of each payment.
        accounts = (journal._get_journal_inbound_outstanding_payment_accounts()
                    | journal._get_journal_outbound_outstanding_payment_accounts())
        items = self.env['account.move.line'].search(self._base_domain(options) + [
            ('journal_id', '=', journal.id), ('reconciled', '=', False),
            ('account_id', '!=', journal.default_account_id.id),
            '|', ('account_id', 'in', accounts.ids),
            '&', ('move_id.origin_payment_id', '!=', False),
            ('account_id.account_type', 'not in', ('asset_receivable', 'liability_payable')),
        ]).filtered(lambda l: (l.balance > 0) == inbound)
        payments = self.env['account.payment'].search([
            ('journal_id', '=', journal.id), ('move_id', '=', False),
            ('state', '=', 'paid'), ('is_matched', '=', False),
            ('date', '<=', fields.Date.to_string(options['date_to'])),
            ('payment_type', '=', 'inbound' if inbound else 'outbound')])
        return items, payments

    def _unreconciled(self, journal, options):
        """Statement lines of the journal not reconciled yet."""
        return self.env['account.bank.statement.line'].search([
            ('journal_id', '=', journal.id), ('is_reconciled', '=', False),
            ('state', '=', 'posted'),
            ('date', '<=', fields.Date.to_string(options['date_to']))])

    def _figures(self, journal, options):
        receipts, receipt_payments = self._outstanding(journal, options, True)
        payments, payment_payments = self._outstanding(journal, options, False)
        unreconciled = self._unreconciled(journal, options)
        statement = sum(self._statement_items(journal, options).mapped('balance'))
        books = sum(self._book_items(journal, options).mapped('balance'))
        open_receipts = sum(receipts.mapped('amount_residual')) \
            + sum(receipt_payments.mapped('amount_company_currency_signed'))
        open_payments = sum(payments.mapped('amount_residual')) \
            + sum(payment_payments.mapped('amount_company_currency_signed'))
        not_reconciled = sum(unreconciled.move_id.line_ids.filtered(
            lambda l: l.account_id == journal.default_account_id).mapped('balance'))
        return {
            'statement': statement, 'receipts': open_receipts, 'payments': open_payments,
            'adjusted_bank': statement + open_receipts + open_payments,
            'books': books - not_reconciled + open_receipts + open_payments,
            'unreconciled': not_reconciled,
            'adjusted_books': books + open_receipts + open_payments,
        }

    def _lines(self, options):
        lines = []
        for journal in self._bank_journals(options):
            figures = self._figures(journal, options)
            jid = journal.id

            def row(key, name, value, unfoldable=False, css=''):
                return {'id': '%s_%s' % (key, jid), 'name': name, 'level': 1,
                        'columns': [value], 'unfoldable': unfoldable, 'class': css}
            difference = figures['adjusted_bank'] - figures['adjusted_books']
            lines += [
                {'id': 'journal_%s' % jid, 'name': '%s - %s' % (journal.code, journal.name),
                 'level': 0, 'columns': [''], 'class': 'main'},
                row('statement', _("Balance as per bank statement"), figures['statement']),
                row('receipts', _("Receipts not yet on the bank statement"), figures['receipts'],
                    unfoldable=True),
                row('payments', _("Payments not yet on the bank statement"), figures['payments'],
                    unfoldable=True),
                row('adjustedbank', _("Adjusted bank balance"), figures['adjusted_bank'], css='section'),
                row('books', _("Balance as per books"), figures['books']),
                row('unreconciled', _("Bank transactions not yet reconciled"), figures['unreconciled'],
                    unfoldable=True),
                row('adjustedbooks', _("Adjusted book balance"), figures['adjusted_books'], css='section'),
                dict(row('difference', _("Difference"), difference), level=0, **{'class': 'total'}),
            ]
        return lines

    def _child_lines(self, options, line_id):
        kind, _sep, jid = line_id.partition('_')
        journal = self.env['account.journal'].browse(int(jid)).exists() if jid.isdigit() else None
        if not journal or kind not in ('receipts', 'payments', 'unreconciled'):
            return []
        children = []
        if kind == 'unreconciled':
            for st_line in self._unreconciled(journal, options):
                liquidity = st_line.move_id.line_ids.filtered(
                    lambda l: l.account_id == journal.default_account_id)[:1]
                children.append(self._child(line_id, 'aml_%s' % liquidity.id, (
                    st_line.date, st_line.payment_ref, st_line.partner_id.name), liquidity.balance))
            return children
        items, payments = self._outstanding(journal, options, kind == 'receipts')
        for item in items:
            children.append(self._child(line_id, 'aml_%s' % item.id, (
                item.date, item.move_id.name, item.partner_id.name, item.name), item.amount_residual))
        for payment in payments:
            children.append(self._child(line_id, 'payment_%s' % payment.id, (
                payment.date, payment.name, payment.partner_id.name), payment.amount_company_currency_signed))
        return children

    @staticmethod
    def _child(parent_id, line_id, parts, amount):
        return {'id': line_id, 'name': ' - '.join(str(p) for p in parts if p), 'level': 2,
                'parent_id': parent_id, 'columns': [amount]}

    def _line_action(self, options, line_id):
        if line_id.startswith('payment_'):
            payment = self.env['account.payment'].browse(int(line_id.split('_')[1])).exists()
            return payment and {'type': 'ir.actions.act_window', 'res_model': 'account.payment',
                                'res_id': payment.id, 'views': [(False, 'form')], 'target': 'current'}
        return super()._line_action(options, line_id)
