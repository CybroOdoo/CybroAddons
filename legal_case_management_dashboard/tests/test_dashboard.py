###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,line-too-long,import-error,no-name-in-module
from contextlib import contextmanager
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from odoo import fields, http
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.legal_case_management_dashboard.controllers.legal_case_management_dashboard import (
    LegalCaseDashboard,
)


@contextmanager
def mock_request(env, uid=None):
    """Context manager to bind request in Odoo 20 contextvars."""
    mock = MagicMock()
    mock.env = env
    if uid is not None:
        mock.env.uid = uid
    token = http.request_var.set(mock)
    try:
        yield mock
    finally:
        http.request_var.reset(token)


@tagged('post_install', '-at_install')
class TestLegalCaseDashboard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if hasattr(cls.env['res.partner'], '_check_email'):
            patcher = patch.object(
                type(cls.env['res.partner']),
                '_check_email',
                lambda self: True,
            )
            patcher.start()
            cls.addClassCleanup(patcher.stop)

        cls.company = cls.env.company

        # Create Client Partner
        cls.client = cls.env['res.partner'].create({
            'name': 'Test Dashboard Client',
            'email': 'dashclient@example.com',
            'phone': '9876543210',
            'company_id': cls.company.id,
        })

        # Create Judge Partner
        cls.judge = cls.env['res.partner'].create({
            'name': 'Judge Judy',
            'is_judge': True,
            'is_judge_unavailable': False,
        })

        # Create Court
        cls.court = cls.env['legal.court'].create({
            'name': 'District Court Dashboard',
            'judge_id': cls.judge.id,
        })

        # Create Lawyer Employee
        cls.lawyer = cls.env['hr.employee'].create({
            'name': 'Senior Dashboard Lawyer',
            'is_lawyer': True,
            'wage_per_case': 1500,
            'wage_per_trial': 300,
            'not_available': False,
            'company_id': cls.company.id,
        })

        # Create Case Category
        cls.category = cls.env['case.category'].create({
            'name': 'Corporate Dashboard Law',
        })

        # Create Case Registration
        start_date = fields.Date.today() - timedelta(days=40)
        cls.case = cls.env['case.registration'].create({
            'client_id': cls.client.id,
            'case_category_id': cls.category.id,
            'court_id': cls.court.id,
            'lawyer_id': cls.lawyer.id,
            'description': '<p>Dashboard Case Test</p>',
            'payment_method': 'case',
            'start_date': start_date,
            'company_id': cls.company.id,
            'state': 'draft',
        })

        # Create Second Case in 'won' state
        cls.case_won = cls.env['case.registration'].create({
            'client_id': cls.client.id,
            'case_category_id': cls.category.id,
            'court_id': cls.court.id,
            'lawyer_id': cls.lawyer.id,
            'description': '<p>Dashboard Won Case</p>',
            'payment_method': 'case',
            'start_date': start_date,
            'company_id': cls.company.id,
            'state': 'won',
        })

        # Create Evidence
        cls.evidence = cls.env['legal.evidence'].create({
            'case_id': cls.case.id,
            'in_favor_id': cls.client.id,
            'description': 'Test Dashboard Evidence',
        })

        # Create Trial
        cls.trial = cls.env['legal.trial'].create({
            'case_id': cls.case.id,
            'client_id': cls.client.id,
            'trial_date': fields.Datetime.now(),
        })

        # Create Invoice linked to case
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.client.id,
            'company_id': cls.company.id,
            'case_ref': cls.case.name,
            'invoice_date': fields.Date.today() - timedelta(days=15),
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Case Retainer Fee',
                    'quantity': 1,
                    'price_unit': 2500.0,
                }),
            ],
        })

        cls.controller = LegalCaseDashboard()

    def test_01_date_filter(self):
        """Test calculation of date filters."""
        res = self.controller.date_filter()
        self.assertIn('first_day_of_last_month', res)
        self.assertIn('last_day_of_last_month', res)
        self.assertIn('first_day_of_six_months_ago', res)
        self.assertIn('first_day_of_twelve_months_ago', res)
        self.assertIsInstance(res['first_day_of_last_month'], date)
        self.assertIsInstance(res['last_day_of_last_month'], date)
        self.assertIsInstance(res['first_day_of_six_months_ago'], date)
        self.assertIsInstance(res['first_day_of_twelve_months_ago'], date)
        self.assertLess(res['first_day_of_last_month'], res['last_day_of_last_month'] + timedelta(days=1))

    def test_02_add_lawyer_selection_field(self):
        """Test fetching lawyer selection list."""
        with mock_request(self.env):
            res = self.controller.add_lawyer_selection_field()
            self.assertIsInstance(res, list)
            lawyer_ids = [lawyer['id'] for lawyer in res]
            self.assertIn(self.lawyer.id, lawyer_ids)

    def test_03_get_legal_case_dashboard_values(self):
        """Test fetching comprehensive dashboard statistics."""
        with mock_request(self.env):
            res = self.controller.get_legal_case_dashboard_values(current_company_id=self.company.id)
            self.assertIsInstance(res, dict)
            self.assertIn('total_case', res)
            self.assertGreaterEqual(res['total_case'], 2)
            self.assertIn('total_invoiced', res)
            self.assertGreaterEqual(res['total_invoiced'], 2500.0)
            self.assertIn('lawyers', res)
            self.assertIn('evidences', res)
            self.assertIn('trials', res)
            self.assertIn('clients', res)
            self.assertIn('case_category', res)
            self.assertIn('stage_count', res)
            self.assertIn('data_list', res)
            self.assertIn('top_10_cases', res)

    def test_04_fetch_dashboard_without_filter_value(self):
        """Test dashboard values without filter."""
        with mock_request(self.env):
            res = self.controller.fetch_dashboard_without_filter_value(current_company_id=self.company.id)
            self.assertIsInstance(res, dict)
            self.assertIn('total_case', res)
            self.assertIn('total_invoiced', res)
            self.assertIn('lawyers', res)
            self.assertIn('evidences', res)
            self.assertIn('trials', res)
            self.assertIn('clients', res)
            self.assertGreaterEqual(res['total_case'], 2)

    def test_05_fetch_dashboard_filter_value(self):
        """Test dashboard filter value across various combinations."""
        with mock_request(self.env):
            # Filter: Admin lawyer, specific stage
            data1 = {'stage': 'draft', 'lawyer': 'admin'}
            res1 = self.controller.fetch_dashboard_filter_value(data=data1)
            self.assertIn('total_case', res1)
            self.assertIn(self.case.id, res1['total_case'])

            # Filter: Specific lawyer, won stage
            data2 = {'stage': 'won', 'lawyer': str(self.lawyer.id)}
            res2 = self.controller.fetch_dashboard_filter_value(data=data2)
            self.assertIn(self.case_won.id, res2['total_case'])

            # Filter: Admin lawyer, month_wise = last_month
            data3 = {'stage': False, 'lawyer': 'admin', 'month_wise': 'last_month'}
            res3 = self.controller.fetch_dashboard_filter_value(data=data3)
            self.assertIsInstance(res3['total_case'], list)

            # Filter: Specific lawyer, month_wise = last_6_months
            data4 = {'stage': 'draft', 'lawyer': self.lawyer.id, 'month_wise': 'last_6_months'}
            res4 = self.controller.fetch_dashboard_filter_value(data=data4)
            self.assertIsInstance(res4['total_case'], list)

            # Filter: Admin lawyer, month_wise = last_12_months
            data5 = {'stage': '', 'lawyer': 'admin', 'month_wise': 'last_12_months'}
            res5 = self.controller.fetch_dashboard_filter_value(data=data5)
            self.assertIsInstance(res5['total_case'], list)
