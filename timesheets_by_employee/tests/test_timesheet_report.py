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
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTimesheetReport(TransactionCase):
    """Test suite for the Timesheet PDF Report wizard and report parser."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        standard_layout = cls.env.ref('web.external_layout_standard', raise_if_not_found=False)
        if standard_layout:
            cls.env.company.external_report_layout_id = standard_layout

        cls.test_user = cls.env['res.users'].create({
            'name': 'Timesheet Test User',
            'login': 'timesheet_test_user@example.com',
            'email': 'timesheet_test_user@example.com',
        })
        cls.test_employee = cls.env['hr.employee'].create({
            'name': 'Timesheet Test Employee',
            'user_id': cls.test_user.id,
        })
        cls.test_project = cls.env['project.project'].create({
            'name': 'Timesheet Test Project',
        })
        cls.today = fields.Date.context_today(cls.test_user)
        cls.yesterday = cls.today - timedelta(days=1)
        cls.two_days_ago = cls.today - timedelta(days=2)
        cls.tomorrow = cls.today + timedelta(days=1)

        # Create sample timesheet lines
        cls.line_1 = cls.env['account.analytic.line'].create({
            'name': 'Development Task 1',
            'project_id': cls.test_project.id,
            'employee_id': cls.test_employee.id,
            'user_id': cls.test_user.id,
            'date': cls.two_days_ago,
            'unit_amount': 5.0,
        })
        cls.line_2 = cls.env['account.analytic.line'].create({
            'name': 'Review Task 2',
            'project_id': cls.test_project.id,
            'employee_id': cls.test_employee.id,
            'user_id': cls.test_user.id,
            'date': cls.yesterday,
            'unit_amount': 3.5,
        })

    def test_wizard_creation(self):
        """Test creating a timesheet.report wizard record."""
        wizard = self.env['timesheet.report'].create({
            'user_id': self.test_user.id,
            'from_date': self.two_days_ago,
            'to_date': self.today,
        })
        self.assertEqual(wizard.user_id, self.test_user)
        self.assertEqual(wizard.from_date, self.two_days_ago)
        self.assertEqual(wizard.to_date, self.today)

    def test_wizard_date_validation_future_from_date(self):
        """Test that a future from_date raises UserError."""
        wizard = self.env['timesheet.report'].create({
            'user_id': self.test_user.id,
            'from_date': self.tomorrow,
            'to_date': self.tomorrow,
        })
        with self.assertRaises(UserError):
            wizard.print_timesheet()

    def test_wizard_date_validation_future_to_date(self):
        """Test that a future to_date raises UserError."""
        wizard = self.env['timesheet.report'].create({
            'user_id': self.test_user.id,
            'from_date': self.yesterday,
            'to_date': self.tomorrow,
        })
        with self.assertRaises(UserError):
            wizard.print_timesheet()

    def test_wizard_date_validation_start_after_end(self):
        """Test that start date after end date raises UserError."""
        wizard = self.env['timesheet.report'].create({
            'user_id': self.test_user.id,
            'from_date': self.today,
            'to_date': self.two_days_ago,
        })
        with self.assertRaises(UserError):
            wizard.print_timesheet()

    def test_wizard_print_timesheet_action(self):
        """Test that print_timesheet returns the expected report action."""
        wizard = self.env['timesheet.report'].create({
            'user_id': self.test_user.id,
            'from_date': self.two_days_ago,
            'to_date': self.today,
        })
        action = wizard.print_timesheet()
        if action.get('type') == 'ir.actions.act_window' and 'report_action' in action.get('context', {}):
            action = action['context']['report_action']

        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(
            action.get('report_name'),
            'timesheets_by_employee.report_timesheet_employee',
        )
        self.assertIn('data', action)
        self.assertEqual(action['data']['employee'], self.test_user.id)
        self.assertEqual(action['data']['start_date'], self.two_days_ago)
        self.assertEqual(action['data']['end_date'], self.today)

    def test_report_values_with_timesheets(self):
        """Test _get_report_values computation with timesheets present."""
        report_model = self.env['report.timesheets_by_employee.report_timesheet_employee']
        data = {
            'employee': self.test_user.id,
            'start_date': self.two_days_ago,
            'end_date': self.today,
        }
        res = report_model._get_report_values(docids=[], data=data)
        self.assertIn('data', res)
        report_data = res['data']
        self.assertEqual(report_data['employee_name'], self.test_employee.name)
        self.assertEqual(report_data['total'], 8.5)
        self.assertEqual(len(report_data['timesheets']), 2)
        expected_period = f"From {self.two_days_ago} To {self.today}"
        self.assertEqual(report_data['period'], expected_period)

    def test_report_values_date_filtering(self):
        """Test that date filters correctly restrict timesheet records."""
        report_model = self.env['report.timesheets_by_employee.report_timesheet_employee']
        # Filter only for yesterday
        data = {
            'employee': self.test_user.id,
            'start_date': self.yesterday,
            'end_date': self.yesterday,
        }
        res = report_model._get_report_values(docids=[], data=data)
        report_data = res['data']
        self.assertEqual(len(report_data['timesheets']), 1)
        self.assertEqual(report_data['total'], 3.5)
        self.assertEqual(report_data['timesheets'][0]['duration'], 3.5)

    def test_report_values_period_variations(self):
        """Test period text computation with start-only, end-only, and all."""
        report_model = self.env['report.timesheets_by_employee.report_timesheet_employee']

        # Start date only
        data_start_only = {'employee': self.test_user.id, 'start_date': self.two_days_ago}
        res = report_model._get_report_values(docids=[], data=data_start_only)
        self.assertEqual(res['data']['period'], f"From {self.two_days_ago}")

        # End date only
        data_end_only = {'employee': self.test_user.id, 'end_date': self.today}
        res = report_model._get_report_values(docids=[], data=data_end_only)
        self.assertEqual(res['data']['period'], f"To {self.today}")

        # Neither date
        data_neither = {'employee': self.test_user.id}
        res = report_model._get_report_values(docids=[], data=data_neither)
        self.assertEqual(res['data']['period'], 'All')

    def test_report_values_without_employee_in_data(self):
        """Test _get_report_values fallback when no employee is provided in data."""
        report_model = self.env['report.timesheets_by_employee.report_timesheet_employee']
        res = report_model._get_report_values(docids=[], data={})
        self.assertIn('data', res)
        self.assertEqual(res['data']['employee_name'], self.env.user.name)

    def test_report_qweb_rendering(self):
        """Test that QWeb report renders successfully with correct content."""
        data = {
            'employee': self.test_user.id,
            'start_date': self.two_days_ago,
            'end_date': self.today,
        }
        html_content, _ = self.env['ir.actions.report']._render_qweb_html(
            'timesheets_by_employee.action_report_print_timesheets',
            [self.test_user.id],
            data=data,
        )
        self.assertTrue(html_content)
        self.assertIn(b'Timesheet Report by Employees', html_content)
        self.assertIn(b'Timesheet Test Employee', html_content)
        self.assertIn(b'Timesheet Test Project', html_content)
