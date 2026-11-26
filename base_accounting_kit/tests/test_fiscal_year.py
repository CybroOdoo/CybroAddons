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
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import new_test_user, tagged

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestFiscalYear(AccountingKitTestCommon):
    """P2.3-b: Fiscal Year records, the dates core and the reports use,
    closing / reopening with the Global Lock Date, rights."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.write({'fiscalyear_last_day': 31, 'fiscalyear_last_month': '12'})
        cls.Year = cls.env['kit.fiscal.year']
        users = {}
        for role, group in (('chief', 'base_accounting_kit.group_account_chief'),
                            ('accountant', 'account.group_account_user')):
            users[role] = new_test_user(
                cls.env, login='kit_fy_%s' % role, groups='%s,base.group_user' % group,
                company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.users = users

    def make(self, start, end, **vals):
        return self.Year.create(dict(company_id=self.company.id, date_from=start, date_to=end, **vals))

    def close(self, year, **vals):
        """Close Year: the wizard with its defaults, then Close."""
        action = year.action_close()
        self.assertEqual(action['res_model'], 'kit.year.closing')
        wizard = self.env['kit.year.closing'].with_context(action['context']).create(vals)
        wizard.action_close()
        return wizard

    def dates(self, day):
        res = self.company.compute_fiscalyear_dates(day)
        return res['date_from'], res['date_to']

    def test_dates_follow_the_records(self):
        """A 15-month year is used for its dates (also by the P&L "This
        Financial Year"); other dates follow the company setting, trimmed
        so they do not overlap a record; the name is proposed."""
        y = self.year
        first = self.make(date(y - 1, 10, 1), date(y, 12, 31))
        self.assertEqual(first.name, 'FY %s-%s' % (y - 1, str(y)[2:]))
        self.assertEqual(self.dates(date(y - 1, 11, 5)), (date(y - 1, 10, 1), date(y, 12, 31)))
        self.assertEqual(self.dates(date(y, 6, 30)), (date(y - 1, 10, 1), date(y, 12, 31)))
        self.assertEqual(self.dates(date(y - 1, 3, 1)), (date(y - 1, 1, 1), date(y - 1, 9, 30)))
        self.assertEqual(self.dates(date(y + 1, 3, 1)), (date(y + 1, 1, 1), date(y + 1, 12, 31)))
        options = self.dyn('financial').get_report({
            'account_report_id': self.env.ref('base_accounting_kit.account_financial_report_profitandloss0').id,
            'date_preset': 'this_year'})['options']
        self.assertEqual((options['date_from'], options['date_to']), (date(y - 1, 10, 1), date(y, 12, 31)))
        self.assertEqual(self.year_named(date(y + 1, 1, 1), date(y + 1, 12, 31)).name, 'FY %s' % (y + 1))

    def year_named(self, start, end):
        return self.make(start, end)

    def test_no_overlap(self):
        """Years of a company cannot overlap or be longer than 24 months."""
        self.make(date(self.year - 1, 1, 1), date(self.year - 1, 12, 31))
        with self.assertRaises(ValidationError):
            self.make(date(self.year - 1, 6, 1), date(self.year, 5, 31))
        with self.assertRaises(ValidationError):
            self.make(date(self.year, 1, 1), date(self.year + 2, 6, 30))

    def test_close_and_reopen(self):
        """Close in order sets the Global Lock Date; a closed year cannot
        change or be deleted; Reopen (last year only) gives the lock date
        back; not under the Hard Lock Date."""
        y = self.year
        old = self.make(date(y - 3, 1, 1), date(y - 3, 12, 31))
        prev = self.make(date(y - 2, 1, 1), date(y - 2, 12, 31))
        with self.assertRaises(UserError):
            self.close(prev)
        self.close(old)
        self.close(prev)
        self.assertEqual((old.state, prev.state), ('closed', 'closed'))
        self.assertEqual(self.company.fiscalyear_lock_date, date(y - 2, 12, 31))
        self.assertEqual(prev.lock_date_before, date(y - 3, 12, 31))
        with self.assertRaises(UserError):
            prev.date_to = date(y - 2, 11, 30)
        with self.assertRaises(UserError):
            prev.unlink()
        with self.assertRaises(UserError):
            old.action_reopen()
        prev.action_reopen()
        self.assertEqual(prev.state, 'open')
        self.assertEqual(self.company.fiscalyear_lock_date, date(y - 3, 12, 31))
        self.company.hard_lock_date = date(y - 3, 6, 30)
        with self.assertRaises(UserError):
            old.action_reopen()

    def test_reopen_with_later_lock_date(self):
        """Reopen refuses when the Global Lock Date was moved after the
        year meanwhile."""
        fy = self.make(date(self.year - 2, 1, 1), date(self.year - 2, 12, 31))
        self.close(fy)
        self.company.fiscalyear_lock_date = date(self.year - 1, 3, 31)
        with self.assertRaises(UserError):
            fy.action_reopen()

    def test_create_next_year(self):
        """Create Next Year: the year of today first, then the 12 months
        after the last year."""
        action = self.Year.action_create_next_year()
        first = self.Year.browse(action['res_id'])
        self.assertEqual((first.date_from, first.date_to), (date(self.year, 1, 1), date(self.year, 12, 31)))
        second = self.Year.browse(self.Year.action_create_next_year()['res_id'])
        self.assertEqual((second.date_from, second.date_to), (date(self.year + 1, 1, 1), date(self.year + 1, 12, 31)))

    def test_rights(self):
        """Chief Accountants create and close years; Accountants only read."""
        chief = self.Year.with_user(self.users['chief']).with_context(allowed_company_ids=self.company.ids)
        fy = chief.create({'date_from': date(self.year - 2, 1, 1), 'date_to': date(self.year - 2, 12, 31)})
        self.assertEqual(fy.company_id, self.company)
        accountant = self.Year.with_user(self.users['accountant']).with_context(allowed_company_ids=self.company.ids)
        self.assertEqual(accountant.search([]), fy.with_user(self.users['accountant']))
        with self.assertRaises(AccessError):
            accountant.create({'date_from': date(self.year - 1, 1, 1), 'date_to': date(self.year - 1, 12, 31)})
        with self.assertRaises(UserError):
            fy.with_user(self.users['accountant']).action_close()
        self.close(fy)
        self.assertEqual(self.company.fiscalyear_lock_date, date(self.year - 2, 12, 31))


@tagged('post_install', '-at_install')
class TestYearClosing(AccountingKitTestCommon):
    """P2.3-c: Year-end Closing: checks, the entry moving the result from
    Current Year Earnings to Retained Earnings (P&L unchanged, equity
    unchanged), Reopen reversing it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.write({'fiscalyear_last_day': 31, 'fiscalyear_last_month': '12'})
        y = cls.year - 1
        cls.fy = cls.env['kit.fiscal.year'].create({
            'company_id': cls.company.id, 'date_from': date(y, 1, 1), 'date_to': date(y, 12, 31)})
        cls.income = cls.kit_account('income')
        cls.expense = cls.kit_account('expense')
        cls.receivable = cls.kit_account('asset_receivable')
        cls.retained = cls.env['account.account'].create({
            'name': 'Kit Retained Earnings', 'code': 'KITRE1', 'account_type': 'equity',
            'company_ids': [Command.set(cls.company.ids)]})
        cls.earnings = cls.company.get_unaffected_earnings_account()
        cls.pl = cls.env.ref('base_accounting_kit.account_financial_report_profitandloss0')
        cls.bs = cls.env.ref('base_accounting_kit.account_financial_report_balancesheet0')
        cls.equity_sum = cls.env.ref('base_accounting_kit.account_financial_report_equitysum0')

    def wizard(self, **vals):
        action = self.fy.action_close()
        return self.env['kit.year.closing'].with_context(action['context']).create(
            dict({'retained_account_id': self.retained.id}, **vals))

    def book(self, income, expense, day=None):
        day = day or date(self.year - 1, 6, 30)
        self.kit_entry(day, [(self.receivable, income, 0), (self.income, 0, income)])
        self.kit_entry(day, [(self.expense, expense, 0), (self.receivable, 0, expense)])

    def figure(self, report, line_id):
        data = self.dyn('financial').get_report({
            'account_report_id': report.id, 'date_preset': 'custom',
            'date_from': '%s-01-01' % (self.year - 1), 'date_to': '%s-12-31' % (self.year - 1)})
        return next(line['columns'][0] for line in data['lines'] if line['id'] == line_id)

    def test_closing_entry(self):
        """Income 1,000, expenses 400: the entry moves 600 from Current Year
        Earnings to Retained Earnings at the year end; the P&L still shows
        600; total equity does not change; Reopen reverses it."""
        self.book(1000, 400)
        equity_before = self.figure(self.bs, 'total_%s' % self.equity_sum.id)
        wizard = self.wizard()
        self.assertEqual((wizard.income, wizard.expense, wizard.result), (1000, 400, 600))
        self.assertEqual(wizard.earnings_account_id, self.earnings)
        wizard.action_close()
        move = self.fy.closing_move_id
        self.assertEqual(self.fy.state, 'closed')
        self.assertEqual((move.state, move.date), ('posted', date(self.year - 1, 12, 31)))
        self.assertRecordValues(move.line_ids.sorted('debit'), [
            {'account_id': self.retained.id, 'debit': 0, 'credit': 600},
            {'account_id': self.earnings.id, 'debit': 600, 'credit': 0}])
        self.assertEqual(self.company.kit_retained_earnings_account_id, self.retained)
        self.assertEqual(self.company.fiscalyear_lock_date, date(self.year - 1, 12, 31))
        self.assertAmount(self.figure(self.pl, 'report_%s' % self.pl.id), 600)
        self.assertAmount(self.figure(self.bs, 'total_%s' % self.equity_sum.id), equity_before)
        self.fy.action_reopen()
        self.assertEqual((self.fy.state, self.fy.closing_move_id.id), ('open', False))
        self.assertEqual(move.reversal_move_ids.state, 'posted')
        self.assertFalse(self.company.fiscalyear_lock_date)
        self.assertAmount(self.figure(self.bs, 'total_%s' % self.equity_sum.id), equity_before)
        balance = sum(self.env['account.move.line'].search([('account_id', '=', self.retained.id)]).mapped('balance'))
        self.assertAmount(balance, 0)

    def test_balance_sheet_after_closing(self):
        """P1.14: after closing last year, the Balance Sheet of this year
        balances (the closing entry on Current Year Earnings nets the
        closed result, "Profit (Loss) to report" is not counted twice), and
        so does a comparison period inside the closed year."""
        self.book(1000, 400)
        self.wizard().action_close()
        self.kit_entry(date(self.year, 3, 1), [(self.receivable, 250, 0), (self.income, 0, 250)])
        data = self.dyn('financial').get_report({
            'account_report_id': self.bs.id, 'date_preset': 'custom',
            'date_from': '%s-01-01' % self.year, 'date_to': '%s-12-31' % self.year,
            'comparison': {'periods': 1}})
        lines = self.by_id(data)
        root = lines.get('total_%s' % self.bs.id) or lines['report_%s' % self.bs.id]
        self.assertAmount(root['columns'][0], 0)
        self.assertAmount(root['columns'][1], 0)
        equity = lines['total_%s' % self.equity_sum.id]['columns']
        self.assertAmount(equity[0], 850)
        self.assertAmount(equity[1], 600)

    def test_loss_and_zero(self):
        """A loss is moved the other way; a zero result posts nothing."""
        self.book(300, 500)
        self.wizard().action_close()
        self.assertRecordValues(self.fy.closing_move_id.line_ids.sorted('debit'), [
            {'account_id': self.earnings.id, 'debit': 0, 'credit': 200},
            {'account_id': self.retained.id, 'debit': 200, 'credit': 0}])
        nxt = self.env['kit.fiscal.year'].create({
            'company_id': self.company.id, 'date_from': date(self.year, 1, 1), 'date_to': date(self.year, 12, 31)})
        wizard = self.env['kit.year.closing'].with_context(default_fiscal_year_id=nxt.id).create({})
        self.assertEqual(wizard.result, 0)
        wizard.action_close()
        self.assertEqual(nxt.state, 'closed')
        self.assertFalse(nxt.closing_move_id)

    def test_checks(self):
        """Draft entries block until "Close anyway"; unreconciled bank
        transactions and an earlier open year always block."""
        self.book(100, 0)
        self.kit_entry(date(self.year - 1, 5, 1), [(self.expense, 10, 0), (self.receivable, 0, 10)], post=False)
        wizard = self.wizard()
        self.assertEqual(wizard.draft_count, 1)
        self.assertTrue(wizard.has_warnings and not wizard.has_blocking)
        self.assertEqual(wizard.with_context(check='draft').action_open_check()['res_model'], 'account.move')
        with self.assertRaises(UserError):
            wizard.action_close()
        bank = self.kit_journal('bank')
        self.env['account.bank.statement.line'].create({
            'journal_id': bank.id, 'date': date(self.year - 1, 7, 1), 'amount': 50, 'payment_ref': 'kit open'})
        wizard = self.wizard(close_anyway=True)
        self.assertEqual(wizard.unreconciled_count, 1)
        with self.assertRaises(UserError):
            wizard.action_close()
        self.assertEqual(self.fy.state, 'open')
        older = self.env['kit.fiscal.year'].create({
            'company_id': self.company.id, 'date_from': date(self.year - 2, 1, 1), 'date_to': date(self.year - 2, 12, 31)})
        self.assertEqual(self.wizard().open_year_count, 1)
        self.assertTrue(older)
