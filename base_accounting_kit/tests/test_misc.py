# -*- coding: utf-8 -*-
from datetime import date
from odoo.tests import tagged
from .common import AccountKitCommon


@tagged('post_install', '-at_install')
class TestMisc(AccountKitCommon):

    def test_common_report_base_registered(self):
        """The module-owned account.common.report base exists and its fields
        are inherited by the report wizards (the A1 rebase)."""
        self.assertIn('account.common.report', self.env)
        wizard_fields = self.env['account.balance.report']._fields
        for fname in ('company_id', 'journal_ids', 'date_from', 'date_to',
                      'target_move'):
            self.assertIn(fname, wizard_fields,
                          "%s must be inherited from account.common.report" % fname)

    def test_financial_report_level_is_recursive(self):
        """account.financial.report.level is a recursive stored compute."""
        pnl = self.env.ref(
            'base_accounting_kit.account_financial_report_profitandloss0')
        self.assertEqual(pnl.level, 0, "Root report is level 0")
        if pnl.children_ids:
            self.assertTrue(
                all(child.level == 1 for child in pnl.children_ids),
                "Direct children are one level deeper")

    def test_lock_date_wizard_sets_company_lock(self):
        """The lock-date wizard writes the lock date onto the company."""
        wizard = self.env['account.lock.date'].create({
            'company_id': self.env.company.id,
            'sale_lock_date': '2019-01-01',
        })
        wizard.execute()
        self.assertEqual(self.env.company.sale_lock_date, date(2019, 1, 1))

    def test_asset_category_create_multi(self):
        """Asset categories can be created in batch (model_create_multi)."""
        cats = self.env['account.asset.category'].create([
            {'name': 'Cat A', 'price': 100.0,
             'account_asset_id': self.asset_account.id,
             'account_depreciation_id': self.asset_account.id,
             'account_depreciation_expense_id': self.expense_account.id,
             'journal_id': self.misc_journal.id, 'method_period': 12,
             'method_time': 'number', 'type': 'purchase'},
            {'name': 'Cat B', 'price': 200.0,
             'account_asset_id': self.asset_account.id,
             'account_depreciation_id': self.asset_account.id,
             'account_depreciation_expense_id': self.expense_account.id,
             'journal_id': self.misc_journal.id, 'method_period': 12,
             'method_time': 'number', 'type': 'purchase'},
        ])
        self.assertEqual(len(cats), 2)
