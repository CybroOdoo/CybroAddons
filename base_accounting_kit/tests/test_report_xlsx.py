# -*- coding: utf-8 -*-
"""XLSX export tests for the accounting reports.

Each report wizard exposes ``action_print_xlsx`` returning an
``ir.actions.report`` of ``report_type == 'xlsx'``; the ``/xlsx_report``
controller then calls ``get_xlsx_report(options, response)`` to stream the
workbook. These tests exercise both halves in-process and assert a valid
workbook comes out, plus the Scope-B comparison columns on GL / Trial Balance.
"""
import io
import json

import openpyxl
from odoo import Command
from odoo.tests import tagged
from .common import AccountKitCommon


class _FakeResponse:
    """Minimal stand-in for the werkzeug response the controller passes."""
    def __init__(self):
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestReportXlsx(AccountKitCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.init_invoice('out_invoice', partner=cls.partner_a,
                         invoice_date='2020-02-01', amounts=[1000.0],
                         taxes=[], post=True)
        cls.init_invoice('in_invoice', partner=cls.partner_b,
                         invoice_date='2020-02-05', amounts=[400.0],
                         taxes=[], post=True)
        cls.menu = cls.env['ir.ui.menu'].search([], limit=1)
        cls.journals = cls.env['account.journal'].search(
            [('company_id', '=', cls.env.company.id)])
        cls.pnl = cls.env.ref(
            'base_accounting_kit.account_financial_report_profitandloss0')
        cls.cash_flow_root = cls.env.ref(
            'base_accounting_kit.account_financial_report_cash_flow0')

    def _run(self, model, vals):
        """Create the wizard, run its xlsx export end-to-end, assert a valid
        workbook is produced and return the parsed table dict."""
        ctx = dict(active_model='ir.ui.menu', active_id=self.menu.id,
                   active_ids=self.menu.ids)
        wizard = self.env[model].with_context(**ctx).create(vals)
        action = wizard.action_print_xlsx()
        self.assertEqual(action.get('report_type'), 'xlsx')
        self.assertEqual(action['data']['model'], model)
        table = json.loads(action['data']['options'])
        # Stream the workbook exactly like the controller does.
        response = _FakeResponse()
        self.env[model].get_xlsx_report(table, response)
        raw = response.stream.getvalue()
        self.assertTrue(raw.startswith(b'PK'), "Output is a valid xlsx (zip)")
        # openpyxl parses it back -> the workbook is well-formed.
        openpyxl.load_workbook(io.BytesIO(raw))
        return table

    def _dates(self, **extra):
        vals = {'date_from': '2020-01-01', 'date_to': '2020-12-31',
                'target_move': 'posted', 'journal_ids': [
                    Command.set(self.journals.ids)]}
        vals.update(extra)
        return vals

    def test_financial_report_xlsx(self):
        """P&L exports a workbook with a balance column."""
        table = self._run('financial.report', self._dates(
            account_report_id=self.pnl.id))
        labels = [c['label'] for c in table['columns']]
        self.assertIn('Balance', labels)
        self.assertTrue(table['rows'])

    def test_general_ledger_xlsx(self):
        """General ledger exports a workbook."""
        table = self._run('account.report.general.ledger', self._dates(
            display_account='all'))
        self.assertEqual(table['columns'][0]['label'], 'Date')

    def test_general_ledger_comparison_column(self):
        """Enabling comparison adds the comparison column + compute works."""
        table = self._run('account.report.general.ledger', self._dates(
            display_account='all', enable_filter=True,
            date_from_cmp='2019-01-01', date_to_cmp='2019-12-31'))
        labels = [c['label'] for c in table['columns']]
        self.assertIn('Comparison Balance', labels)

    def test_trial_balance_xlsx(self):
        """Trial balance exports a workbook ending with a totals row."""
        table = self._run('account.balance.report', self._dates(
            display_account='all', journal_ids=False))
        self.assertEqual(table['rows'][-1]['cells'][1], 'Total')
        self.assertTrue(table['rows'][-1]['bold'])

    def test_trial_balance_comparison_columns(self):
        """Comparison adds Comparison + Variance columns."""
        table = self._run('account.balance.report', self._dates(
            display_account='all', journal_ids=False, enable_filter=True,
            date_from_cmp='2019-01-01', date_to_cmp='2019-12-31'))
        labels = [c['label'] for c in table['columns']]
        self.assertIn('Comparison Balance', labels)
        self.assertIn('Variance', labels)

    def test_partner_ledger_xlsx(self):
        """Partner ledger exports a workbook."""
        self._run('account.report.partner.ledger', self._dates(
            result_selection='customer', reconciled=True))

    def test_aged_partner_xlsx(self):
        """Aged partner balance exports a workbook with bucket columns."""
        table = self._run('account.aged.trial.balance', self._dates(
            result_selection='customer', date_from='2020-12-31',
            period_length=30))
        labels = [c['label'] for c in table['columns']]
        self.assertEqual(labels[0], 'Partner')
        self.assertEqual(labels[1], 'Not Due')

    def test_tax_report_xlsx(self):
        """Tax report exports a workbook."""
        self._run('kit.account.tax.report', self._dates())

    def test_cash_flow_xlsx(self):
        """Cash flow statement exports a workbook."""
        self._run('cash.flow.report', self._dates(
            account_report_id=self.cash_flow_root.id, filter_cmp='filter_no'))

    def test_bank_book_xlsx(self):
        """Bank book exports a workbook."""
        self._run('account.bank.book.report', self._dates(
            display_account='all'))

    def test_cash_book_xlsx(self):
        """Cash book exports a workbook."""
        self._run('account.cash.book.report', self._dates(
            display_account='all'))

    def test_day_book_xlsx(self):
        """Day book exports a workbook (entries grouped by date)."""
        self._run('account.day.book.report', self._dates(
            date_from='2020-02-01', date_to='2020-02-28'))

    def test_journal_audit_xlsx(self):
        """Journal audit exports a workbook."""
        self._run('account.print.journal', self._dates(
            sort_selection='date'))
