# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R(odoo@cybrosys.com)
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
###############################################################################
from datetime import date, timedelta
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError
from odoo import fields


@tagged('post_install', '-at_install')
class TestAccountMoveDashboard(TransactionCase):
    """
    Test suite for the account.move dashboard extension.
    Validates KPI calculations, period handling, and permission checks.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up test environment and initialize basic model variables
        needed across various dashboard functional tests.
        """
        super().setUpClass()
        cls.move_model = cls.env['account.move']
        cls.user = cls.env.user
        cls.company = cls.env.company

    def test_dashboard_check_group(self):
        """Test access control based on groups."""
        # Current user is admin, should have 'account.group_account_readonly'
        group_readonly = 'account.group_account_readonly'
        if not self.user.has_group(group_readonly):
            self.user.write({'group_ids': [(4, self.env.ref(group_readonly).id)]})

        # Should not raise exception
        self.move_model._dashboard_check_group([group_readonly])

        # Test failure (non-existent group)
        with self.assertRaises(AccessError):
            self.move_model._dashboard_check_group(['non_existent.group'])

    def test_dashboard_get_period(self):
        """Test the _dashboard_get_period method returns correct dates."""
        today = fields.Date.context_today(self.move_model)

        # This month
        d_from, d_to = self.move_model._dashboard_get_period('this_month')
        self.assertEqual(d_from, today.replace(day=1))
        self.assertEqual(d_to, today)

        # Last month
        d_from, d_to = self.move_model._dashboard_get_period('last_month')
        expected_d_to = today.replace(day=1) - timedelta(days=1)
        expected_d_from = expected_d_to.replace(day=1)
        self.assertEqual(d_from, expected_d_from)
        self.assertEqual(d_to, expected_d_to)

        # This year
        d_from, d_to = self.move_model._dashboard_get_period('this_year')
        self.assertEqual(d_from, date(today.year, 1, 1))
        self.assertEqual(d_to, today)

        # Custom period
        d_from, d_to = self.move_model._dashboard_get_period('custom', '2023-01-01', '2023-12-31')
        self.assertEqual(d_from, date(2023, 1, 1))
        self.assertEqual(d_to, date(2023, 12, 31))

    def test_dashboard_prev_period(self):
        """Test the _dashboard_prev_period calculation."""
        date_from = date(2023, 2, 1)
        date_to = date(2023, 2, 28)
        
        prev_from, prev_to = self.move_model._dashboard_prev_period(date_from, date_to)
        
        self.assertEqual(prev_to, date(2023, 1, 31))
        self.assertEqual(prev_from, date(2023, 1, 4)) # 28 days back from 31st

    def test_get_dashboard_kpi_data(self):
        """Test get_dashboard_kpi_data returns correct keys without crashing."""
        # Ensure user has the required group to bypass check
        group_invoice = self.env.ref('account.group_account_invoice')
        self.user.write({'group_ids': [(4, group_invoice.id)]})

        params = {
            'period': 'this_month',
            'company_ids': [self.company.id],
        }
        data = self.move_model.get_dashboard_kpi_data(params)
        
        # Check that the basic structure is returned
        self.assertIn('invoices', data)
        self.assertIn('bills', data)
        self.assertIn('overdue_receivable', data)
        self.assertIn('overdue_payable', data)
        self.assertIn('currency_id', data)
        self.assertIn('currency_symbol', data)
        self.assertIn('period', data)

    def test_safe_change_pct(self):
        """Test safe percentage change calculation."""
        pct = self.move_model._safe_change_pct(150, 100)
        self.assertEqual(pct, 50.0)

        pct = self.move_model._safe_change_pct(50, 100)
        self.assertEqual(pct, -50.0)

        pct = self.move_model._safe_change_pct(100, 0)
        self.assertEqual(pct, 0.0)

        pct = self.move_model._safe_change_pct(0, 100)
        self.assertEqual(pct, -100.0)

        # Handling negative previous (e.g. expenses as negative)
        pct = self.move_model._safe_change_pct(150, -100)
        self.assertEqual(pct, 250.0)
