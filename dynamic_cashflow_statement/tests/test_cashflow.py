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
#############################################################################
from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestCashFlow(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.cashflow = cls.env['cashflow']
        cls.company = cls.env.company

        # Find or create a liquidity account (account_type = 'asset_cash')
        cls.cash_account = cls.env['account.account'].search([
            ('account_type', '=', 'asset_cash'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.cash_account:
            cls.cash_account = cls.env['account.account'].create({
                'name': 'Test Cash Account',
                'code': '101099',
                'account_type': 'asset_cash',
                'company_ids': [Command.link(cls.company.id)],
            })

        # Find or create a counterpart account (e.g. income)
        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].create({
                'name': 'Test Income Account',
                'code': '400099',
                'account_type': 'income',
                'company_ids': [Command.link(cls.company.id)],
            })

        # Find or create a cash/bank journal
        cls.journal = cls.env['account.journal'].search([
            ('type', 'in', ('bank', 'cash')),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Test Cash Journal',
                'type': 'cash',
                'code': 'TCASH',
                'company_id': cls.company.id,
            })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Demo Cash Flow Partner',
        })

        # 1. Posted Cash-In move (Debit 1000.0 on Cash Account)
        cls.move_in = cls.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': cls.journal.id,
            'date': '2026-05-10',
            'line_ids': [
                (0, 0, {
                    'name': 'Cash Inflow Line',
                    'account_id': cls.cash_account.id,
                    'partner_id': cls.partner.id,
                    'debit': 1000.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': 'Income Counterpart Line',
                    'account_id': cls.income_account.id,
                    'partner_id': cls.partner.id,
                    'debit': 0.0,
                    'credit': 1000.0,
                }),
            ],
        })
        cls.move_in.action_post()

        # 2. Posted Cash-Out move (Credit 400.0 on Cash Account)
        cls.move_out = cls.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': cls.journal.id,
            'date': '2026-05-20',
            'line_ids': [
                (0, 0, {
                    'name': 'Expense Counterpart Line',
                    'account_id': cls.income_account.id,
                    'partner_id': cls.partner.id,
                    'debit': 400.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': 'Cash Outflow Line',
                    'account_id': cls.cash_account.id,
                    'partner_id': cls.partner.id,
                    'debit': 0.0,
                    'credit': 400.0,
                }),
            ],
        })
        cls.move_out.action_post()

        # 3. Draft Move (should be ignored by the report)
        cls.move_draft = cls.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': cls.journal.id,
            'date': '2026-05-15',
            'line_ids': [
                (0, 0, {
                    'name': 'Draft Cash Inflow',
                    'account_id': cls.cash_account.id,
                    'partner_id': cls.partner.id,
                    'debit': 250.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': 'Draft Income Counterpart',
                    'account_id': cls.income_account.id,
                    'partner_id': cls.partner.id,
                    'debit': 0.0,
                    'credit': 250.0,
                }),
            ],
        })

        # Test users for access rights verification
        cls.accounting_user = cls.env['res.users'].create({
            'name': 'Accounting Readonly User',
            'login': 'acc_user_test',
            'email': 'acc_user_test@example.com',
            'group_ids': [
                Command.set([
                    cls.env.ref('base.group_user').id,
                    cls.env.ref('account.group_account_readonly').id,
                ])
            ],
        })

        cls.regular_user = cls.env['res.users'].create({
            'name': 'Regular Internal User',
            'login': 'reg_user_test',
            'email': 'reg_user_test@example.com',
            'group_ids': [
                Command.set([cls.env.ref('base.group_user').id])
            ],
        })

    def test_get_report_values_structure_and_totals(self):
        """Test report data structure, totals, and exclusion of draft moves."""
        result = self.cashflow.get_report_values()

        self.assertIn('fetched_data', result)
        self.assertIn('account_res', result)
        self.assertIsInstance(result['account_res'], list)

        # Locate our test cash account
        account_data = next(
            (acc for acc in result['account_res'] if acc['account'] == self.cash_account.name),
            None
        )
        self.assertIsNotNone(account_data, "Cash account should be present in report values")
        self.assertEqual(account_data['code'], self.cash_account.code)

        # Verify totals include posted inflow (1000) and outflow (400)
        self.assertGreaterEqual(account_data['total_debit'], 1000.0)
        self.assertGreaterEqual(account_data['total_credit'], 400.0)

        # Verify move lines contain posted moves, and draft moves are excluded
        move_ids = [line['move_id'] for line in account_data['move_lines']]
        self.assertIn(self.move_in.id, move_ids)
        self.assertIn(self.move_out.id, move_ids)
        self.assertNotIn(self.move_draft.id, move_ids, "Draft entries must be excluded")

        # Verify journal breakdown
        journal_data = next(
            (j for j in account_data['journal_lines'] if j['id'] == self.journal.id),
            None
        )
        self.assertIsNotNone(journal_data, "Journal lines should contain test journal")
        self.assertGreaterEqual(journal_data['total_debit'], 1000.0)
        self.assertGreaterEqual(journal_data['total_credit'], 400.0)

    def test_date_filters(self):
        """Test date_from and date_to filtering in report values."""
        # 1. Filter up to 2026-05-15: include move_in (2026-05-10), exclude move_out (2026-05-20)
        res_early = self.cashflow.get_report_values({
            'date_from': '2026-05-01',
            'date_to': '2026-05-15',
        })
        account_early = next(
            (acc for acc in res_early['account_res'] if acc['account'] == self.cash_account.name),
            None
        )
        self.assertIsNotNone(account_early)
        move_ids_early = [line['move_id'] for line in account_early['move_lines']]
        self.assertIn(self.move_in.id, move_ids_early)
        self.assertNotIn(self.move_out.id, move_ids_early)

        # 2. Filter from 2026-05-16: include move_out (2026-05-20), exclude move_in (2026-05-10)
        res_late = self.cashflow.get_report_values({
            'date_from': '2026-05-16',
            'date_to': '2026-05-31',
        })
        account_late = next(
            (acc for acc in res_late['account_res'] if acc['account'] == self.cash_account.name),
            None
        )
        self.assertIsNotNone(account_late)
        move_ids_late = [line['move_id'] for line in account_late['move_lines']]
        self.assertNotIn(self.move_in.id, move_ids_late)
        self.assertIn(self.move_out.id, move_ids_late)

        # 3. Filter outside the active range
        res_past = self.cashflow.get_report_values({
            'date_from': '2020-01-01',
            'date_to': '2020-01-31',
        })
        account_past = next(
            (acc for acc in res_past['account_res'] if acc['account'] == self.cash_account.name),
            None
        )
        if account_past:
            move_ids_past = [line['move_id'] for line in account_past['move_lines']]
            self.assertNotIn(self.move_in.id, move_ids_past)
            self.assertNotIn(self.move_out.id, move_ids_past)

    def test_company_filter(self):
        """Test company_ids filter."""
        res_company = self.cashflow.get_report_values({
            'company_ids': [self.company.id],
        })
        account_data = next(
            (acc for acc in res_company['account_res'] if acc['account'] == self.cash_account.name),
            None
        )
        self.assertIsNotNone(account_data)

        # Empty company list should return no accounts
        res_no_company = self.cashflow.get_report_values({
            'company_ids': [],
        })
        self.assertEqual(len(res_no_company['account_res']), 0)

    def test_access_rights(self):
        """Test that accounting users can read report and non-accounting internal users are blocked."""
        # Accounting user should have access
        res = self.cashflow.with_user(self.accounting_user).get_report_values()
        self.assertIn('account_res', res)

        # Regular user without accounting access should be denied
        with self.assertRaises(AccessError):
            self.cashflow.with_user(self.regular_user).get_report_values()
