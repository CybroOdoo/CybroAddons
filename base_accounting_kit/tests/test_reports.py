# -*- coding: utf-8 -*-
from odoo.tests import tagged
from .common import AccountKitCommon


@tagged('post_install', '-at_install')
class TestReports(AccountKitCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Posted data so the report SQL has something to aggregate.
        cls.init_invoice('out_invoice', partner=cls.partner_a,
                         invoice_date='2020-02-01', amounts=[1000.0],
                         taxes=[], post=True)
        cls.init_invoice('in_invoice', partner=cls.partner_a,
                         invoice_date='2020-02-05', amounts=[400.0],
                         taxes=[], post=True)
        cls.report_ctx = {
            'date_from': '2020-01-01', 'date_to': '2020-12-31',
            'state': 'posted', 'strict_range': True,
            'company_id': cls.env.company.id,
        }
        cls.accounts = cls.env['account.account'].search(
            [('company_ids', 'in', cls.env.company.id)])

    def _book_entry(self, model_name):
        model = self.env[model_name].with_context(**self.report_ctx)
        # init_balance=True exercises the (previously broken) initial-balance
        # sub-query as well as the main query.
        return model._get_account_move_entry(
            self.accounts, True, 'sort_date', 'all')

    def test_general_ledger_runs_with_initial_balance(self):
        """GL report SQL (main + initial-balance) runs without error."""
        res = self._book_entry('report.base_accounting_kit.report_general_ledger')
        self.assertIsInstance(res, list)

    def test_bank_book_runs_with_initial_balance(self):
        """Bank book report SQL runs without error."""
        res = self._book_entry('report.base_accounting_kit.report_bank_book')
        self.assertIsInstance(res, list)

    def test_cash_book_runs_with_initial_balance(self):
        """Cash book report SQL runs without error."""
        res = self._book_entry('report.base_accounting_kit.report_cash_book')
        self.assertIsInstance(res, list)

    def test_trial_balance_runs(self):
        """Trial balance report SQL runs without error."""
        model = self.env['report.base_accounting_kit.report_trial_balance'] \
            .with_context(**self.report_ctx)
        res = model._get_accounts(self.accounts, 'all')
        self.assertIsInstance(res, list)

    def test_financial_report_pnl_runs(self):
        """The Profit & Loss financial report builds its lines (runs the
        _query_get-based balance SQL)."""
        wizard = self.env['financial.report'].create({
            'account_report_id': self.env.ref(
                'base_accounting_kit.account_financial_report_profitandloss0').id,
            'date_from': '2020-01-01',
            'date_to': '2020-12-31',
            'target_move': 'posted',
        })
        menu = self.env['ir.ui.menu'].search([], limit=1)
        # view_report_pdf builds the report lines (runs the _query_get-based
        # balance SQL). Returning without error is the real assertion here.
        action = wizard.with_context(
            active_model='ir.ui.menu', active_id=menu.id,
            active_ids=menu.ids).view_report_pdf()
        self.assertIsInstance(action, dict)
