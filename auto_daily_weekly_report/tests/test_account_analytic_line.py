# -*- coding: utf-8 -*-
import datetime
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.mail.tests.common import MockEmail


@tagged('at_install', 'post_install')
class TestAccountAnalyticLine(TransactionCase, MockEmail):

    @classmethod
    def setUpClass(cls):
        super(TestAccountAnalyticLine, cls).setUpClass()
        cls._init_mail_gateway()

    def setUp(self):
        super(TestAccountAnalyticLine, self).setUp()
        # Create a user for the manager and employee
        self.manager_user = self.env['res.users'].create({
            'name': 'Test Manager User',
            'login': 'manager_user',
            'email': 'manager@test.com',
        })
        self.employee_user = self.env['res.users'].create({
            'name': 'Test Employee User',
            'login': 'employee_user',
            'email': 'employee@test.com',
        })

        # Create a calendar with working days
        self.calendar = self.env['resource.calendar'].create({
            'name': 'Standard Calendar',
            'attendance_ids': [
                (0, 0, {'name': 'Monday Morning', 'dayofweek': '0', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Monday Afternoon', 'dayofweek': '0', 'hour_from': 13, 'hour_to': 17, 'day_period': 'afternoon'}),
                (0, 0, {'name': 'Tuesday Morning', 'dayofweek': '1', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Wednesday Morning', 'dayofweek': '2', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Thursday Morning', 'dayofweek': '3', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
                (0, 0, {'name': 'Friday Morning', 'dayofweek': '4', 'hour_from': 8, 'hour_to': 12, 'day_period': 'morning'}),
            ]
        })

        self.manager = self.env['hr.employee'].create({
            'name': 'Test Manager',
            'work_email': 'manager@test.com',
            'user_id': self.manager_user.id,
            'resource_calendar_id': self.calendar.id,
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
            'work_email': 'employee@test.com',
            'parent_id': self.manager.id,
            'user_id': self.employee_user.id,
            'resource_calendar_id': self.calendar.id,
        })
        self.project = self.env['project.project'].search([('allow_timesheets', '=', True)], limit=1)
        if not self.project:
            # Fallback if no project exists (try/except for missing module registry vs DB constraints)
            try:
                self.project = self.env['project.project'].create({
                    'name': 'Test Project',
                    'allow_timesheets': True,
                })
            except ValueError:
                # If sale_timesheet is in DB but not registry
                self.project = self.env['project.project'].create({
                    'name': 'Test Project',
                    'allow_timesheets': True,
                    'billing_type': 'not_billable',
                })
        
        self.task = self.env['project.task'].search([('project_id', '=', self.project.id)], limit=1)
        if not self.task:
            self.task = self.env['project.task'].create({
                'name': 'Test Task',
                'project_id': self.project.id,
            })

    def test_create_daily_report(self):
        """Test daily report creation and email sending."""
        # Create analytic line for today
        self.env['account.analytic.line'].create({
            'name': 'Description 1',
            'project_id': self.project.id,
            'task_id': self.task.id,
            'employee_id': self.employee.id,
            'unit_amount': 2.0,
            'date': datetime.datetime.today().date(),
        })

        # Capture emails sent
        with self.mock_mail_gateway():
            self.env['account.analytic.line'].create_daily_report()

        # Check if an email was sent
        # We need to find the correct email based on the recipient
        emails = self._mails
        employee_email = self.employee.work_email
        manager_email = self.manager.work_email
        
        # Filter emails where to_email matches manager_email
        relevant_emails = [e for e in emails if manager_email in (e.get('email_to') or [])]
        self.assertTrue(len(relevant_emails) >= 1, "Email was not sent to the manager.")

    def test_create_weekly_report(self):
        """Test weekly report creation and email sending."""
        # Create analytic line for this week
        today = datetime.datetime.today().date()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        
        self.env['account.analytic.line'].create({
            'name': 'Weekly Description',
            'project_id': self.project.id,
            'task_id': self.task.id,
            'employee_id': self.employee.id,
            'unit_amount': 8.0,
            'date': start_of_week,
        })

        # Capture emails sent
        with self.mock_mail_gateway():
            self.env['account.analytic.line'].create_weekly_report()

        # Check if an email was sent
        emails = self._mails
        manager_email = self.manager.work_email
        relevant_emails = [e for e in emails if manager_email in (e.get('email_to') or [])]
        self.assertTrue(len(relevant_emails) >= 1, "Weekly email was not sent to the manager.")
