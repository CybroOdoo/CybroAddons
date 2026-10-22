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
from datetime import date

from freezegun import freeze_time

from odoo.addons.mail.tests.common import MailCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
@freeze_time('2026-10-21 10:00:00')  # Wednesday, week 43
class TestTaskReport(MailCase):
    """Tests for the daily and weekly task report emails."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = cls.env['hr.employee'].create({
            'name': 'Manager',
            'work_email': 'adwr.manager@test.example.com',
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Employee',
            'work_email': 'adwr.employee@test.example.com',
            'parent_id': cls.manager.id,
        })
        cls.project = cls.env['project.project'].create({'name': 'Website'})
        cls.task = cls.env['project.task'].create({
            'name': 'Home Page',
            'project_id': cls.project.id,
        })
        cls.line_model = cls.env['account.analytic.line']

    def _log_time(self, day, description, hours=2.0, employee=None):
        """Create a timesheet line for the employee on the given day."""
        return self.line_model.create({
            'name': description,
            'date': day,
            'project_id': self.project.id,
            'task_id': self.task.id,
            'employee_id': (employee or self.employee).id,
            'unit_amount': hours,
        })

    def _report_mails(self, subject, employee=None):
        """Return the report emails with the given subject sent by the employee.

        Demo employees may get reports too, so only the test employee's
        emails are returned.
        """
        sender = (employee or self.employee).work_email
        return self._new_mails.filtered(
            lambda mail: subject in (mail.subject or '') and mail.email_from == sender)

    def _recipients(self, mail):
        """Return the email addresses the mail is sent to.

        The template's email_to may be stored as recipient partners.
        """
        return mail.recipient_ids.mapped('email') + (
            [mail.email_to] if mail.email_to else [])

    # Daily report

    def test_daily_report_sent(self):
        """Today's timesheets are emailed to the employee's manager."""
        self._log_time(date(2026, 10, 21), 'Header design', 3.5)
        self._log_time(date(2026, 10, 21), 'Footer design', 1.0)
        self._log_time(date(2026, 10, 20), 'Yesterday work')
        with self.mock_mail_gateway():
            self.line_model.create_daily_report()
        mail = self._report_mails('Daily Work Report')
        self.assertEqual(len(mail), 1)
        self.assertEqual(mail.subject, 'Daily Work Report - Employee')
        self.assertEqual(mail.email_from, 'adwr.employee@test.example.com')
        self.assertEqual(self._recipients(mail), ['adwr.manager@test.example.com'])
        self.assertIn('Header design', mail.body_html)
        self.assertIn('Footer design', mail.body_html)
        self.assertIn('Website', mail.body_html)
        self.assertIn('Home Page', mail.body_html)
        self.assertIn('3.5', mail.body_html)
        self.assertNotIn('Yesterday work', mail.body_html)

    def test_daily_report_without_timesheet(self):
        """No email is sent when nothing was logged today."""
        self._log_time(date(2026, 10, 20), 'Yesterday work')
        with self.mock_mail_gateway():
            self.line_model.create_daily_report()
        self.assertFalse(self._report_mails('Daily Work Report'))

    def test_daily_report_without_manager(self):
        """Employees without a manager get no report."""
        self._log_time(date(2026, 10, 21), 'Manager work', employee=self.manager)
        with self.mock_mail_gateway():
            self.line_model.create_daily_report()
        self.assertFalse(self._report_mails('Daily Work Report', self.manager))

    def test_daily_report_per_employee(self):
        """Each employee's report only holds their own timesheets."""
        other = self.env['hr.employee'].create({
            'name': 'Other Employee',
            'work_email': 'adwr.other@test.example.com',
            'parent_id': self.manager.id,
        })
        self._log_time(date(2026, 10, 21), 'Employee task')
        self._log_time(date(2026, 10, 21), 'Other task', employee=other)
        with self.mock_mail_gateway():
            self.line_model.create_daily_report()
        mail = self._report_mails('Daily Work Report')
        other_mail = self._report_mails('Daily Work Report', other)
        self.assertEqual(len(mail), 1)
        self.assertEqual(len(other_mail), 1)
        self.assertIn('Employee task', mail.body_html)
        self.assertNotIn('Other task', mail.body_html)
        self.assertIn('Other task', other_mail.body_html)
        self.assertNotIn('Employee task', other_mail.body_html)

    def test_report_manager_without_email(self):
        """No report is sent when the manager has no work email."""
        self.manager.work_email = False
        self._log_time(date(2026, 10, 21), 'Header design')
        with self.mock_mail_gateway():
            self.line_model.create_daily_report()
            self.line_model.create_weekly_report()
        self.assertFalse(self._report_mails('Work Report'))

    def test_report_employee_without_email(self):
        """An employee without email sends from the company address."""
        self.env.company.email = 'adwr.company@test.example.com'
        self.employee.work_email = False
        self._log_time(date(2026, 10, 21), 'Header design')
        with self.mock_mail_gateway():
            self.line_model.create_daily_report()
        mail = self._new_mails.filtered(
            lambda m: m.subject == 'Daily Work Report - Employee')
        self.assertEqual(len(mail), 1)
        self.assertIn('adwr.company@test.example.com', mail.email_from)
        self.assertEqual(self._recipients(mail), ['adwr.manager@test.example.com'])

    def test_report_without_template(self):
        """Deleted email templates do not break the scheduled actions."""
        self.env.ref('auto_daily_weekly_report.email_template_daily_report').unlink()
        self.env.ref('auto_daily_weekly_report.email_template_weekly_report').unlink()
        self._log_time(date(2026, 10, 21), 'Header design')
        with self.mock_mail_gateway():
            self.line_model.create_daily_report()
            self.line_model.create_weekly_report()
        self.assertFalse(self._report_mails('Work Report'))

    # Weekly report

    def test_weekly_report_sent(self):
        """This week's timesheets are emailed to the manager."""
        self._log_time(date(2026, 10, 19), 'Monday work')
        self._log_time(date(2026, 10, 21), 'Wednesday work')
        with self.mock_mail_gateway():
            self.line_model.create_weekly_report()
        mail = self._report_mails('Weekly Work Report')
        self.assertEqual(len(mail), 1)
        self.assertEqual(mail.subject, 'Weekly Work Report - Employee - 2026-10-21')
        self.assertEqual(mail.email_from, 'adwr.employee@test.example.com')
        self.assertEqual(self._recipients(mail), ['adwr.manager@test.example.com'])
        self.assertIn('Week 43, 2026', mail.body_html)
        self.assertIn('Monday work', mail.body_html)
        self.assertIn('Wednesday work', mail.body_html)

    def test_weekly_report_excludes_other_weeks(self):
        """Timesheets from the previous week are not included."""
        self._log_time(date(2026, 10, 16), 'Last Friday work')
        self._log_time(date(2026, 10, 20), 'Tuesday work')
        with self.mock_mail_gateway():
            self.line_model.create_weekly_report()
        mail = self._report_mails('Weekly Work Report')
        self.assertIn('Tuesday work', mail.body_html)
        self.assertNotIn('Last Friday work', mail.body_html)

    def test_weekly_report_excludes_non_working_days(self):
        """Timesheets on days off in the working schedule are left out."""
        self.assertNotIn('6', self.employee.resource_calendar_id.attendance_ids.mapped('dayofweek'))
        self._log_time(date(2026, 10, 18), 'Sunday work')
        self._log_time(date(2026, 10, 19), 'Monday work')
        with self.mock_mail_gateway():
            self.line_model.create_weekly_report()
        mail = self._report_mails('Weekly Work Report')
        self.assertIn('Monday work', mail.body_html)
        self.assertNotIn('Sunday work', mail.body_html)

    def test_weekly_report_without_timesheet(self):
        """No email is sent when nothing was logged this week."""
        with self.mock_mail_gateway():
            self.line_model.create_weekly_report()
        self.assertFalse(self._report_mails('Weekly Work Report'))

    # Scheduled actions

    def test_cron_jobs(self):
        """The scheduled actions call the report methods."""
        daily = self.env.ref('auto_daily_weekly_report.ir_cron_auto_daily_task_report')
        weekly = self.env.ref('auto_daily_weekly_report.ir_cron_auto_weekly_task_report')
        self.assertEqual(daily.code, 'model.create_daily_report()')
        self.assertEqual(daily.interval_type, 'days')
        self.assertEqual(weekly.code, 'model.create_weekly_report()')
        self.assertEqual(weekly.interval_type, 'weeks')
