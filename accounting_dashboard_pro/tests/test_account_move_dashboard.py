# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
#    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
##############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestAccountMoveDashboard(TransactionCase):
    """Tests for Account Move Dashboard APIs."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and user."""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Create a test user with manager access
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Test Move Dashboard Manager',
            'login': 'test_move_manager',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('account.group_account_manager').id])],
        })

    def test_01_dashboard_kpi_data(self):
        """Test retrieving dashboard KPI data structure."""
        move_model = self.env['account.move']
        params = {
            'period': 'this_month',
            'company_ids': [self.env.company.id],
        }
        
        # Run with manager user
        kpi_data = move_model.with_user(self.user_manager).get_dashboard_kpi_data(params)
        
        # Check standard KPIs exist in output
        expected_keys = [
            'invoices', 'bills', 'overdue_receivable', 'overdue_payable',
            'revenue', 'expenses', 'net_profit', 'cash_balance',
            'total_receivable', 'total_payable', 'net_cash_position',
            'cash_burn_rate', 'runway_days', 'working_capital',
            'gross_margin', 'dso', 'dpo'
        ]
        for key in expected_keys:
            self.assertIn(key, kpi_data)

    def test_02_dashboard_chart_data(self):
        """Test retrieving dashboard chart data."""
        move_model = self.env['account.move']
        params = {
            'period': 'this_month',
            'company_ids': [self.env.company.id],
        }
        
        chart_data = move_model.with_user(self.user_manager).get_dashboard_chart_data(params)
        self.assertIn('labels', chart_data)
        self.assertIn('revenue', chart_data)
        self.assertIn('expenses', chart_data)
        self.assertEqual(len(chart_data['labels']), 12, "Should return 12 months of data")

    def test_03_exclude_bank_lines(self):
        """Test the dummy exclude_bank_lines field to prevent UI crashes."""
        move_line_model = self.env['account.move.line']
        
        # The field should exist in the model's fields
        self.assertIn('exclude_bank_lines', move_line_model._fields)
        
        # The search method should return an empty domain
        domain = move_line_model._search_exclude_bank_lines('=', True)
        self.assertEqual(domain, [])

    def test_04_dashboard_cashflow(self):
        """Test retrieving dashboard cashflow."""
        move_model = self.env['account.move']
        params = {
            'days': 90,
            'company_ids': [self.env.company.id],
        }
        
        cashflow_data = move_model.with_user(self.user_manager).get_dashboard_cashflow(params)
        self.assertIn('labels', cashflow_data)
        self.assertIn('data', cashflow_data)
        self.assertIn('current_balance', cashflow_data)

    def test_05_dashboard_aging(self):
        """Test retrieving dashboard aging."""
        move_model = self.env['account.move']
        params = {
            'type': 'receivable',
            'company_ids': [self.env.company.id],
        }
        
        aging_data = move_model.with_user(self.user_manager).get_dashboard_aging(params)
        self.assertIn('labels', aging_data)
        self.assertIn('data', aging_data)
        self.assertEqual(len(aging_data['data']), 5)

    def test_06_dashboard_top_expenses(self):
        """Test retrieving dashboard top expenses."""
        move_model = self.env['account.move']
        params = {
            'period': 'this_month',
            'limit': 5,
            'company_ids': [self.env.company.id],
        }
        
        expenses_data = move_model.with_user(self.user_manager).get_dashboard_top_expenses(params)
        self.assertIn('labels', expenses_data)
        self.assertIn('data', expenses_data)

    def test_07_dashboard_tax_summary(self):
        """Test retrieving dashboard tax summary."""
        move_model = self.env['account.move']
        params = {
            'period': 'this_month',
            'company_ids': [self.env.company.id],
        }
        
        tax_data = move_model.with_user(self.user_manager).get_dashboard_tax_summary(params)
        self.assertIn('collected', tax_data)
        self.assertIn('paid', tax_data)
        self.assertIn('net', tax_data)

    def test_08_dashboard_lists(self):
        """Test retrieving dashboard lists (overdue, upcoming, recent)."""
        move_model = self.env['account.move']
        params = {
            'limit': 5,
            'company_ids': [self.env.company.id],
        }
        
        lists_data = move_model.with_user(self.user_manager).get_dashboard_lists(params)
        self.assertIn('overdue_invoices', lists_data)
        self.assertIn('upcoming_bills', lists_data)
        self.assertIn('recent_payments', lists_data)

    def test_09_account_journal_ids(self):
        """Test retrieving default journal ids."""
        move_model = self.env['account.move']
        journal_ids = move_model.with_user(self.user_manager).get_account_journal_ids({})
        self.assertIsInstance(journal_ids, list)

    def test_10_dashboard_alerts(self):
        """Test retrieving dashboard alerts."""
        move_model = self.env['account.move']
        params = {
            'company_ids': [self.env.company.id],
        }
        
        alerts_data = move_model.with_user(self.user_manager).get_dashboard_alerts(params)
        self.assertIsInstance(alerts_data, list)
