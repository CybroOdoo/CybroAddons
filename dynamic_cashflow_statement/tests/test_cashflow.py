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
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestCashflow(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.cashflow_model = cls.env['cashflow']

        # Create an account move to have data for testing
        cls.move = cls.env['account.move'].create({
            'move_type': 'entry',
            'date': '2023-01-01',
            'journal_id': cls.company_data['default_journal_misc'].id,
            'line_ids': [
                (0, 0, {
                    'account_id': cls.company_data['default_account_revenue'].id,
                    'name': 'Test Credit',
                    'credit': 100.0,
                    'debit': 0.0,
                }),
                (0, 0, {
                    'account_id': cls.company_data['default_account_receivable'].id,
                    'name': 'Test Debit',
                    'credit': 0.0,
                    'debit': 100.0,
                }),
            ]
        })
        cls.move.action_post()

    def test_get_report_values_returns_structure(self):
        """Test get_report_values returns the expected dictionary keys."""
        report_data = self.cashflow_model.get_report_values()

        self.assertIn('fetched_data', report_data)
        self.assertIn('journal_res', report_data)
        self.assertIn('account_res', report_data)
        self.assertIsInstance(report_data['fetched_data'], list)
        self.assertIsInstance(report_data['journal_res'], list)
        self.assertIsInstance(report_data['account_res'], list)

    def test_get_report_values_fetched_data(self):
        """Test that fetched_data contains posted move data grouped by
        account code with correct debit/credit totals."""
        report_data = self.cashflow_model.get_report_values()

        self.assertTrue(len(report_data['fetched_data']) > 0)

        revenue_account_code = self.company_data[
            'default_account_revenue'].code
        receivable_account_code = self.company_data[
            'default_account_receivable'].code

        codes_in_fetched_data = [
            d['code'] for d in report_data['fetched_data']]
        self.assertIn(revenue_account_code, codes_in_fetched_data)
        self.assertIn(receivable_account_code, codes_in_fetched_data)

        # Verify debit/credit amounts for our specific accounts
        for data in report_data['fetched_data']:
            if data['code'] == revenue_account_code:
                self.assertGreaterEqual(data['total_credit'], 100.0)
            if data['code'] == receivable_account_code:
                self.assertGreaterEqual(data['total_debit'], 100.0)

    def test_get_report_values_account_res(self):
        """Test that account_res is populated from _get_lines for accounts
        that have posted move lines."""
        report_data = self.cashflow_model.get_report_values()

        # account_res should contain entries for accounts with move data
        self.assertIsInstance(report_data['account_res'], list)
        if report_data['account_res']:
            entry = report_data['account_res'][0]
            self.assertIn('account', entry)
            self.assertIn('code', entry)
            self.assertIn('move_lines', entry)
            self.assertIn('journal_lines', entry)

    def test_get_report_values_with_data_arg(self):
        """Test get_report_values when the optional data argument is
        passed (it is forwarded to _get_lines)."""
        report_data = self.cashflow_model.get_report_values(
            data={'some_key': 'some_value'})
        self.assertIn('fetched_data', report_data)
        self.assertIn('journal_res', report_data)
        self.assertIn('account_res', report_data)

    def test_get_lines_with_data(self):
        """Test _get_lines returns correct structure for an account that
        has posted journal entries."""
        account = self.company_data['default_account_revenue']
        lines_data = self.cashflow_model._get_lines(account, data=None)

        self.assertIsNotNone(lines_data)
        self.assertEqual(lines_data['account'], account.name)
        self.assertEqual(lines_data['code'], account.code)
        self.assertIn('move_lines', lines_data)
        self.assertIn('journal_lines', lines_data)
        self.assertTrue(len(lines_data['move_lines']) > 0)
        self.assertTrue(len(lines_data['journal_lines']) > 0)

    def test_get_lines_move_line_fields(self):
        """Test that each move_line dict from _get_lines contains the
        expected fields."""
        account = self.company_data['default_account_revenue']
        lines_data = self.cashflow_model._get_lines(account, data=None)

        self.assertIsNotNone(lines_data)
        move_line = lines_data['move_lines'][0]
        self.assertIn('id', move_line)
        self.assertIn('move_id', move_line)
        self.assertIn('account_id', move_line)
        self.assertIn('total_debit', move_line)
        self.assertIn('total_credit', move_line)
        self.assertIn('move_name', move_line)

    def test_get_lines_journal_line_fields(self):
        """Test that each journal_line dict from _get_lines contains the
        expected fields."""
        account = self.company_data['default_account_revenue']
        lines_data = self.cashflow_model._get_lines(account, data=None)

        self.assertIsNotNone(lines_data)
        journal_line = lines_data['journal_lines'][0]
        self.assertIn('id', journal_line)
        self.assertIn('name', journal_line)
        self.assertIn('total_debit', journal_line)
        self.assertIn('total_credit', journal_line)

    def test_get_lines_returns_none_for_empty_account(self):
        """Test _get_lines returns None for an account with no posted
        journal entries."""
        # Create a brand-new account that has no moves
        empty_account = self.env['account.account'].create({
            'name': 'Test Empty Account',
            'code': 'X99999',
            'account_type': 'asset_current',
        })
        result = self.cashflow_model._get_lines(empty_account, data=None)
        self.assertIsNone(result)

    def test_get_lines_debit_account(self):
        """Test _get_lines returns data for the receivable (debit-side)
        account of our test move."""
        account = self.company_data['default_account_receivable']
        lines_data = self.cashflow_model._get_lines(account, data=None)

        self.assertIsNotNone(lines_data)
        self.assertEqual(lines_data['code'], account.code)

        # The receivable line has debit=100; verify we see a positive total
        move_line = next(
            (l for l in lines_data['move_lines']
             if l['move_id'] == self.move.id), None)
        self.assertIsNotNone(
            move_line, "Receivable move line not found")
        self.assertGreater(move_line['total_debit'], 0)
