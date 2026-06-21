# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

from datetime import datetime, time, timedelta
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHrEmployeeLessHours(TransactionCase):
    """ Test suite for employee less working hour notification module. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Employee = cls.env['hr.employee']
        cls.Attendance = cls.env['hr.attendance']
        cls.Config = cls.env['ir.config_parameter']

        # Setup Company info
        cls.env.company.write({
            'name': 'Test Company',
            'email': 'company_test@example.com',
            'phone': '1234567890',
        })

        # Set Config Parameters
        cls.Config.sudo().set_param(
            'employee_less_working_hour_notification.minimum_working_hour',
            '6.5'
        )
        cls.Config.sudo().set_param(
            'employee_less_working_hour_notification.hr_email',
            'hr_test@example.com'
        )

        # Create Employee Department
        cls.department = cls.env['hr.department'].create({
            'name': 'Test Department',
        })

        # Create Employees
        cls.emp_less_worked = cls.Employee.create({
            'name': 'Employee Less Worked',
            'department_id': cls.department.id,
        })
        cls.emp_more_worked = cls.Employee.create({
            'name': 'Employee More Worked',
            'department_id': cls.department.id,
        })
        cls.emp_no_checkout = cls.Employee.create({
            'name': 'Employee No Checkout',
            'department_id': cls.department.id,
        })
        cls.emp_other_day = cls.Employee.create({
            'name': 'Employee Other Day',
            'department_id': cls.department.id,
        })

        # Setup Attendances
        yesterday = fields.Date.today() - timedelta(days=1)
        two_days_ago = fields.Date.today() - timedelta(days=2)

        # Employee 1: Worked 4 hours yesterday (less than 6.5)
        cls.Attendance.create({
            'employee_id': cls.emp_less_worked.id,
            'check_in': datetime.combine(yesterday, time(8, 0)),
            'check_out': datetime.combine(yesterday, time(12, 0)),
        })

        # Employee 2: Worked 8 hours yesterday (more than 6.5)
        cls.Attendance.create({
            'employee_id': cls.emp_more_worked.id,
            'check_in': datetime.combine(yesterday, time(8, 0)),
            'check_out': datetime.combine(yesterday, time(16, 0)),
        })

        # Employee 3: Checked in yesterday, no check_out (worked_hours = 0)
        cls.Attendance.create({
            'employee_id': cls.emp_no_checkout.id,
            'check_in': datetime.combine(yesterday, time(9, 0)),
            'check_out': False,
        })

        # Employee 4: Worked 4 hours two days ago (different day)
        cls.Attendance.create({
            'employee_id': cls.emp_other_day.id,
            'check_in': datetime.combine(two_days_ago, time(8, 0)),
            'check_out': datetime.combine(two_days_ago, time(12, 0)),
        })

    def test_01_config_settings(self):
        """ Verify that settings are correctly saved to system parameters """
        settings = self.env['res.config.settings'].create({
            'minimum_working_hour': 7.5,
            'hr_email': 'new_hr_test@example.com',
        })
        settings.execute()

        min_hours = self.Config.sudo().get_param(
            'employee_less_working_hour_notification.minimum_working_hour'
        )
        self.assertEqual(float(min_hours), 7.5)

        hr_email = self.Config.sudo().get_param(
            'employee_less_working_hour_notification.hr_email'
        )
        self.assertEqual(hr_email, 'new_hr_test@example.com')

    def test_02_action_generate_list(self):
        """ Verify that less worked and non-checkout employees are notified """
        # Clear any existing emails
        self.env['mail.mail'].search([('model', '=', 'hr.employee')]).unlink()

        # Run generate list
        self.Employee.action_generate_list()

        # Check mail.mail is created
        mail = self.env['mail.mail'].search([
            ('model', '=', 'hr.employee'),
            ('email_to', '=', 'hr_test@example.com'),
        ])
        self.assertEqual(len(mail), 1, "There should be exactly one notification email created.")

        self.assertEqual(mail.email_from, 'company_test@example.com')
        self.assertEqual(mail.subject, 'Employees Having Less Working Hours')

        # Check mail content/body
        body = mail.body_html
        self.assertIn('Employee Less Worked', body)
        self.assertIn('Employee No Checkout', body)
        self.assertNotIn('Employee More Worked', body)
        self.assertNotIn('Employee Other Day', body)
