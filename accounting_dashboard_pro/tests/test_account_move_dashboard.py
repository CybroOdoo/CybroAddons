###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################

from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountMoveDashboard(TransactionCase):
    """Test suite for accounting dashboard methods extended on account.move."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.move_model = cls.env['account.move']
        cls.company = cls.env.company

        # Users with various accounting roles
        cls.user_readonly = cls.env['res.users'].create({
            'name': 'Accountant Readonly User',
            'login': 'readonly_user@example.com',
            'email': 'readonly_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('account.group_account_readonly').id])],
        })
        cls.user_invoice = cls.env['res.users'].create({
            'name': 'Accountant Invoice User',
            'login': 'invoice_user@example.com',
            'email': 'invoice_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('account.group_account_invoice').id])],
        })
        cls.user_basic = cls.env['res.users'].create({
            'name': 'Accountant Basic User',
            'login': 'basic_user@example.com',
            'email': 'basic_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('account.group_account_basic').id])],
        })
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Accountant Manager User',
            'login': 'manager_user@example.com',
            'email': 'manager_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('account.group_account_manager').id])],
        })
        cls.user_no_access = cls.env['res.users'].create({
            'name': 'Unprivileged User',
            'login': 'no_access_user@example.com',
            'email': 'no_access_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        # Partners
        cls.customer = cls.env['res.partner'].create({'name': 'Test Dashboard Customer'})
        cls.vendor = cls.env['res.partner'].create({'name': 'Test Dashboard Vendor'})

        # Accounts
        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
        ], limit=1)
        cls.expense_account = cls.env['account.account'].search([
            ('account_type', 'like', 'expense%'),
        ], limit=1)

        cls.bank_journal = cls.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', cls.company.id),
        ], limit=1)

        today = fields.Date.context_today(cls.move_model)

        # 1. Posted Customer Invoice in current period
        cls.out_invoice_posted = cls.move_model.create({
            'move_type': 'out_invoice',
            'partner_id': cls.customer.id,
            'invoice_date': today,
            'invoice_line_ids': [(0, 0, {
                'name': 'Consulting Service',
                'account_id': cls.income_account.id,
                'price_unit': 1000.0,
                'quantity': 1,
            })],
        })
        cls.out_invoice_posted.action_post()

        # 2. Draft Customer Invoice
        cls.out_invoice_draft = cls.move_model.create({
            'move_type': 'out_invoice',
            'partner_id': cls.customer.id,
            'invoice_date': today,
            'invoice_line_ids': [(0, 0, {
                'name': 'Draft Service',
                'account_id': cls.income_account.id,
                'price_unit': 500.0,
                'quantity': 1,
            })],
        })

        # 3. Posted Vendor Bill in current period
        cls.in_invoice_posted = cls.move_model.create({
            'move_type': 'in_invoice',
            'partner_id': cls.vendor.id,
            'invoice_date': today,
            'invoice_date_due': today,
            'invoice_line_ids': [(0, 0, {
                'name': 'Office Supplies',
                'account_id': cls.expense_account.id,
                'price_unit': 400.0,
                'quantity': 1,
            })],
        })
        cls.in_invoice_posted.action_post()

        # 4. Overdue Customer Invoice (> 30 days overdue)
        overdue_date = today - timedelta(days=45)
        cls.out_invoice_overdue = cls.move_model.create({
            'move_type': 'out_invoice',
            'partner_id': cls.customer.id,
            'invoice_date': overdue_date,
            'invoice_date_due': overdue_date,
            'invoice_line_ids': [(0, 0, {
                'name': 'Overdue Service',
                'account_id': cls.income_account.id,
                'price_unit': 750.0,
                'quantity': 1,
            })],
        })
        cls.out_invoice_overdue.action_post()

        # 5. Customer Credit Note
        cls.out_refund = cls.move_model.create({
            'move_type': 'out_refund',
            'partner_id': cls.customer.id,
            'invoice_date': today,
            'invoice_line_ids': [(0, 0, {
                'name': 'Service Refund',
                'account_id': cls.income_account.id,
                'price_unit': 100.0,
                'quantity': 1,
            })],
        })
        cls.out_refund.action_post()

        # 6. Payment
        if cls.bank_journal:
            cls.test_payment = cls.env['account.payment'].create({
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': cls.customer.id,
                'amount': 300.0,
                'journal_id': cls.bank_journal.id,
            })
            cls.test_payment.action_post()

            # 7. Unreconciled bank statement line
            cls.st_line = cls.env['account.bank.statement.line'].create({
                'journal_id': cls.bank_journal.id,
                'date': today,
                'payment_ref': 'Bank deposit reference',
                'amount': 150.0,
            })

    def test_dashboard_check_group(self):
        """Verify access control checks on dashboard data."""
        # Privileged user succeeds
        self.move_model.with_user(self.user_readonly)._dashboard_check_group('account.group_account_readonly')
        self.move_model.with_user(self.user_manager)._dashboard_check_group([
            'account.group_account_invoice',
            'account.group_account_manager',
        ])

        # Unprivileged user raises AccessError
        with self.assertRaises(AccessError):
            self.move_model.with_user(self.user_no_access)._dashboard_check_group('account.group_account_readonly')

    def test_dashboard_get_period(self):
        """Verify date ranges for all supported period presets."""
        today = fields.Date.context_today(self.move_model)

        periods = [
            'this_month',
            'last_month',
            'this_quarter',
            'last_quarter',
            'this_year',
            'last_year',
        ]
        for p in periods:
            d_from, d_to = self.move_model._dashboard_get_period(p)
            self.assertIsInstance(d_from, date)
            self.assertIsInstance(d_to, date)
            self.assertLessEqual(d_from, d_to)

        # Custom period with strings
        d_from, d_to = self.move_model._dashboard_get_period('custom', '2026-01-01', '2026-01-31')
        self.assertEqual(d_from, date(2026, 1, 1))
        self.assertEqual(d_to, date(2026, 1, 31))

        # Custom period with date objects
        d_from, d_to = self.move_model._dashboard_get_period('custom', date(2026, 2, 1), date(2026, 2, 28))
        self.assertEqual(d_from, date(2026, 2, 1))
        self.assertEqual(d_to, date(2026, 2, 28))

        # Fallback period
        d_from, d_to = self.move_model._dashboard_get_period('invalid_period')
        self.assertEqual(d_from, today.replace(day=1))
        self.assertEqual(d_to, today)

    def test_dashboard_prev_period(self):
        """Verify previous period date calculation."""
        d_from = date(2026, 3, 1)
        d_to = date(2026, 3, 31)
        p_from, p_to = self.move_model._dashboard_prev_period(d_from, d_to)
        self.assertEqual(p_to, date(2026, 2, 28))
        self.assertEqual((d_to - d_from).days, (p_to - p_from).days)

    def test_dashboard_company_ids(self):
        """Verify company ID filtering logic."""
        cids = self.move_model._dashboard_company_ids()
        self.assertIn(self.company.id, cids)

        cids_explicit = self.move_model._dashboard_company_ids([self.company.id, 999999])
        self.assertEqual(cids_explicit, [self.company.id])

    def test_safe_change_pct(self):
        """Verify percentage change calculation."""
        self.assertEqual(self.move_model._safe_change_pct(120, 100), 20.0)
        self.assertEqual(self.move_model._safe_change_pct(80, 100), -20.0)
        self.assertEqual(self.move_model._safe_change_pct(100, 0), 0.0)
        self.assertEqual(self.move_model._safe_change_pct(50, None), 0.0)

    def test_get_dashboard_kpi_data(self):
        """Verify comprehensive KPI calculation across various user roles."""
        params = {'period': 'this_month'}

        # Manager user gets all KPI sections
        res = self.move_model.with_user(self.user_manager).get_dashboard_kpi_data(params)
        self.assertTrue(res['user_groups']['is_manager'])
        self.assertIn('invoices', res)
        self.assertIn('bills', res)
        self.assertIn('overdue_receivable', res)
        self.assertIn('overdue_payable', res)
        self.assertIn('revenue', res)
        self.assertIn('expenses', res)
        self.assertIn('net_profit', res)
        self.assertIn('cash_balance', res)
        self.assertIn('total_receivable', res)
        self.assertIn('total_payable', res)
        self.assertIn('net_cash_position', res)
        self.assertIn('cash_burn_rate', res)
        self.assertIn('runway_days', res)
        self.assertIn('working_capital', res)
        self.assertIn('gross_margin', res)
        self.assertIn('dso', res)
        self.assertIn('dpo', res)
        self.assertIn('unreconciled_count', res)
        self.assertIn('currency_symbol', res)

        # Invoicing user receives invoicing KPIs
        res_inv = self.move_model.with_user(self.user_invoice).get_dashboard_kpi_data(params)
        self.assertIn('invoices', res_inv)
        self.assertIn('bills', res_inv)

        # Readonly user receives financial and cashflow KPIs
        res_ro = self.move_model.with_user(self.user_readonly).get_dashboard_kpi_data(params)
        self.assertIn('revenue', res_ro)
        self.assertIn('cash_balance', res_ro)

        # Basic user receives basic group KPIs
        res_basic = self.move_model.with_user(self.user_basic).get_dashboard_kpi_data(params)
        self.assertIn('cash_balance', res_basic)

    def test_get_dashboard_chart_data(self):
        """Verify 12-month chart data aggregation."""
        params = {'period': 'this_month'}
        data = self.move_model.with_user(self.user_manager).get_dashboard_chart_data(params)
        self.assertIn('labels', data)
        self.assertIn('revenue', data)
        self.assertIn('expenses', data)
        self.assertEqual(len(data['labels']), 12)

    def test_get_dashboard_cashflow(self):
        """Verify cashflow projection calculations."""
        for days in (30, 60, 90):
            res = self.move_model.with_user(self.user_manager).get_dashboard_cashflow({
                'period': 'this_month',
                'days': days,
            })
            self.assertIn('labels', res)
            self.assertIn('data', res)
            self.assertIn('current_balance', res)
            self.assertEqual(len(res['labels']), len(res['data']))

    def test_get_dashboard_aging(self):
        """Verify aging report calculations for receivables and payables."""
        rec = self.move_model.with_user(self.user_manager).get_dashboard_aging({
            'period': 'this_month',
            'type': 'receivable',
        })
        self.assertIn('labels', rec)
        self.assertIn('data', rec)
        self.assertEqual(rec['type'], 'receivable')
        self.assertEqual(len(rec['labels']), 5)

        pay = self.move_model.with_user(self.user_manager).get_dashboard_aging({
            'period': 'this_month',
            'type': 'payable',
        })
        self.assertIn('labels', pay)
        self.assertIn('data', pay)
        self.assertEqual(pay['type'], 'payable')
        self.assertEqual(len(pay['labels']), 5)

    def test_get_dashboard_top_expenses(self):
        """Verify top expenses by account."""
        res = self.move_model.with_user(self.user_manager).get_dashboard_top_expenses({
            'period': 'this_month',
            'limit': 5,
        })
        self.assertIn('labels', res)
        self.assertIn('data', res)

    def test_get_dashboard_tax_summary(self):
        """Verify tax summary calculation."""
        res = self.move_model.with_user(self.user_manager).get_dashboard_tax_summary({
            'period': 'this_month',
        })
        self.assertIn('collected', res)
        self.assertIn('paid', res)
        self.assertIn('net', res)

    def test_get_dashboard_lists(self):
        """Verify operational lists data (overdue invoices, upcoming bills, recent payments)."""
        res = self.move_model.with_user(self.user_manager).get_dashboard_lists({
            'period': 'this_month',
        })
        self.assertIn('overdue_invoices', res)
        self.assertIn('upcoming_bills', res)
        self.assertIn('recent_payments', res)

    def test_get_account_journal_ids(self):
        """Verify default journal IDs retrieval."""
        j_ids = self.move_model.get_account_journal_ids({})
        self.assertIsInstance(j_ids, list)

    def test_get_dashboard_alerts(self):
        """Verify alert feed generation for overdue invoices, bank lines, and bills."""
        alerts = self.move_model.with_user(self.user_manager).get_dashboard_alerts({
            'period': 'this_month',
        })
        self.assertIsInstance(alerts, list)
        for alert in alerts:
            self.assertIn('type', alert)
            self.assertIn('title', alert)
            self.assertIn('action', alert)

    def test_compute_period_dates(self):
        """Verify compute_period_dates output for all period keys."""
        for p in ['this_month', 'last_month', 'this_quarter', 'last_quarter', 'this_year', 'last_year', 'custom']:
            res = self.move_model.compute_period_dates(p)
            self.assertIn('date_from', res)
            self.assertIn('date_to', res)

    def test_get_dashboard_profit_trend(self):
        """Verify 12-month P&L trend chart calculation."""
        res = self.move_model.with_user(self.user_manager).get_dashboard_profit_trend({
            'period': 'this_month',
        })
        self.assertIn('labels', res)
        self.assertIn('revenue', res)
        self.assertIn('expenses', res)
        self.assertIn('net_profit', res)
        self.assertEqual(len(res['labels']), 12)

    def test_get_dashboard_expense_breakdown(self):
        """Verify expense breakdown doughnut chart data."""
        res = self.move_model.with_user(self.user_manager).get_dashboard_expense_breakdown({
            'period': 'this_month',
        })
        self.assertIn('labels', res)
        self.assertIn('amounts', res)

    def test_get_dashboard_budget_vs_actual(self):
        """Verify budget vs actual chart method."""
        res = self.move_model.with_user(self.user_manager).get_dashboard_budget_vs_actual({
            'period': 'this_month',
        })
        self.assertIn('available', res)
        self.assertIn('labels', res)
        self.assertIn('budgeted', res)
        self.assertIn('actual', res)

    def test_get_dashboard_monthly_cashflow_bars(self):
        """Verify monthly cash inflow/outflow bar chart data."""
        res = self.move_model.with_user(self.user_manager).get_dashboard_monthly_cashflow_bars({
            'period': 'this_month',
        })
        self.assertIn('labels', res)
        self.assertIn('inflows', res)
        self.assertIn('outflows', res)
        self.assertEqual(len(res['labels']), 12)

    def test_get_dashboard_cashflow_waterfall(self):
        """Verify cashflow waterfall data."""
        res = self.move_model.with_user(self.user_manager).get_dashboard_cashflow_waterfall({
            'period': 'this_month',
        })
        self.assertIn('labels', res)
        self.assertIn('values', res)
        self.assertIn('types', res)
        self.assertEqual(res['labels'], ['Opening', 'Cash In', 'Cash Out', 'Closing'])

    def test_get_dashboard_journal_balances(self):
        """Verify bank and cash journal balances calculation."""
        res = self.move_model.with_user(self.user_manager).get_dashboard_journal_balances({
            'period': 'this_month',
        })
        self.assertIsInstance(res, list)
        if res:
            j = res[0]
            self.assertIn('journal_id', j)
            self.assertIn('journal_name', j)
            self.assertIn('balances', j)
            self.assertIn('current_balance', j)
