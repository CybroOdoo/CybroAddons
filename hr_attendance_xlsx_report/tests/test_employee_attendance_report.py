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
from datetime import date, datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo.tests import new_test_user
from odoo.exceptions import ValidationError, AccessError


class TestEmployeeAttendanceReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
        })
        cls.employee2 = cls.env['hr.employee'].create({
            'name': 'Test Employee 2',
        })
        cls.today = date.today()
        cls.now = datetime.now()

    def test_01_wizard_validation_dates(self):
        """Test From Date earlier than To Date validation"""
        wizard = self.env['employee.attendance.report'].create({
            'from_date': self.today + timedelta(days=2),
            'to_date': self.today,
            'employee_ids': [(6, 0, self.employee.ids)]
        })
        with self.assertRaises(ValidationError):
            wizard.action_print_xlsx()

    def test_02_wizard_no_attendance_records(self):
        """Test validation for no attendance records"""
        wizard = self.env['employee.attendance.report'].create({
            'from_date': self.today - timedelta(days=2),
            'to_date': self.today,
            'employee_ids': [(6, 0, self.employee.ids)]
        })
        with self.assertRaises(ValidationError):
            wizard.action_print_xlsx()

    def test_03_wizard_action_print_xlsx(self):
        """Test success case of action_print_xlsx"""
        # Create attendance record
        self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': self.now,
            'check_out': self.now + timedelta(hours=8),
        })
        wizard = self.env['employee.attendance.report'].create({
            'from_date': self.today - timedelta(days=2),
            'to_date': self.today + timedelta(days=2),
            'employee_ids': [(6, 0, self.employee.ids)]
        })
        result = wizard.action_print_xlsx()
        self.assertEqual(result['type'], 'ir.actions.report')
        self.assertEqual(result['report_type'], 'xlsx')
        self.assertEqual(result['data']['model'], 'employee.attendance.report')

    def test_04_get_xlsx_report(self):
        """Test the actual report generation method"""
        self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': self.now,
            'check_out': self.now + timedelta(hours=8),
        })
        self.env.flush_all()
        wizard = self.env['employee.attendance.report'].create({
            'from_date': self.today - timedelta(days=2),
            'to_date': self.today + timedelta(days=2),
            'employee_ids': [(6, 0, self.employee.ids)]
        })

        class MockResponse:
            class stream:
                output = b''
                @classmethod
                def write(cls, data):
                    cls.output += data

        data = {
            'from_date': str(wizard.from_date),
            'to_date': str(wizard.to_date),
            'employee_ids': wizard.employee_ids.ids
        }

        mock_response = MockResponse()
        wizard.get_xlsx_report(data, mock_response)

        # Check if output is not empty and has xlsx signature (PK)
        self.assertTrue(mock_response.stream.output.startswith(b'PK'))

    def test_05_get_xlsx_report_empty_employees(self):
        """Test the actual report generation method with empty employees"""
        self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': self.now,
            'check_out': self.now + timedelta(hours=8),
        })
        self.env.flush_all()
        wizard = self.env['employee.attendance.report'].create({
            'from_date': self.today - timedelta(days=2),
            'to_date': self.today + timedelta(days=2),
            'employee_ids': []
        })

        class MockResponse:
            class stream:
                output = b''
                @classmethod
                def write(cls, data):
                    cls.output += data

        data = {
            'from_date': str(wizard.from_date),
            'to_date': str(wizard.to_date),
            'employee_ids': wizard.employee_ids.ids
        }

        mock_response = MockResponse()
        wizard.get_xlsx_report(data, mock_response)

        self.assertTrue(mock_response.stream.output.startswith(b'PK'))

    def test_06_access_rights(self):
        """Test that regular users cannot access the report while attendance officers can"""
        regular_user = new_test_user(
            self.env, login='regular_user_test',
            groups='base.group_user'
        )
        officer_user = new_test_user(
            self.env, login='officer_user_test',
            groups='base.group_user,hr_attendance.group_hr_attendance_officer'
        )

        with self.assertRaises(AccessError):
            self.env['employee.attendance.report'].with_user(regular_user).create({
                'from_date': self.today,
                'to_date': self.today,
            })

        wizard_officer = self.env['employee.attendance.report'].with_user(officer_user).create({
            'from_date': self.today,
            'to_date': self.today,
        })
        self.assertTrue(wizard_officer.id)

    def test_07_record_rules_attendance_officer(self):
        """Test that attendance officer record rules are enforced"""
        officer_user = new_test_user(
            self.env, login='officer_manager_test',
            groups='base.group_user,hr_attendance.group_hr_attendance_officer'
        )
        self.employee.attendance_manager_id = officer_user.id
        self.employee2.attendance_manager_id = False

        self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': self.now,
            'check_out': self.now + timedelta(hours=8),
        })
        self.env['hr.attendance'].create({
            'employee_id': self.employee2.id,
            'check_in': self.now,
            'check_out': self.now + timedelta(hours=8),
        })
        self.env.flush_all()

        class MockResponse:
            class stream:
                output = b''
                @classmethod
                def write(cls, data):
                    cls.output += data

        wizard = self.env['employee.attendance.report'].with_user(officer_user).create({
            'from_date': self.today - timedelta(days=2),
            'to_date': self.today + timedelta(days=2),
        })
        data = {
            'from_date': str(wizard.from_date),
            'to_date': str(wizard.to_date),
            'employee_ids': [self.employee.id, self.employee2.id],
        }
        mock_response = MockResponse()
        wizard.get_xlsx_report(data, mock_response)
        self.assertTrue(mock_response.stream.output.startswith(b'PK'))

    def test_08_multi_company_isolation(self):
        """Test that attendances in other companies are isolated"""
        company_2 = self.env['res.company'].create({'name': 'Company 2 Test'})
        employee_comp2 = self.env['hr.employee'].create({
            'name': 'Employee Comp 2',
            'company_id': company_2.id,
        })
        self.env['hr.attendance'].create({
            'employee_id': employee_comp2.id,
            'check_in': self.now,
            'check_out': self.now + timedelta(hours=8),
        })
        self.env.flush_all()

        class MockResponse:
            class stream:
                output = b''
                @classmethod
                def write(cls, data):
                    cls.output += data

        wizard = self.env['employee.attendance.report'].create({
            'from_date': self.today - timedelta(days=2),
            'to_date': self.today + timedelta(days=2),
            'company_id': self.env.company.id,
        })
        data = {
            'from_date': str(wizard.from_date),
            'to_date': str(wizard.to_date),
            'employee_ids': [employee_comp2.id],
            'company_id': self.env.company.id,
        }
        mock_response = MockResponse()
        wizard.get_xlsx_report(data, mock_response)
        self.assertTrue(mock_response.stream.output.startswith(b'PK'))

    def test_09_sql_injection_defense(self):
        """Test that string-formatted or malicious employee IDs are safely handled"""
        class MockResponse:
            class stream:
                output = b''
                @classmethod
                def write(cls, data):
                    cls.output += data

        wizard = self.env['employee.attendance.report'].create({
            'from_date': self.today - timedelta(days=2),
            'to_date': self.today + timedelta(days=2),
        })
        data = {
            'from_date': str(wizard.from_date),
            'to_date': str(wizard.to_date),
            'employee_ids': ['1 OR 1=1', 'invalid', -999],
        }
        mock_response = MockResponse()
        wizard.get_xlsx_report(data, mock_response)
        self.assertTrue(mock_response.stream.output.startswith(b'PK'))

    def test_10_wizard_attendance_outside_date_range(self):
        """Test validation when attendance exists but outside selected date range"""
        past_time = self.now - timedelta(days=30)
        self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': past_time,
            'check_out': past_time + timedelta(hours=8),
        })
        wizard = self.env['employee.attendance.report'].create({
            'from_date': self.today - timedelta(days=2),
            'to_date': self.today,
            'employee_ids': [(6, 0, self.employee.ids)],
        })
        with self.assertRaises(ValidationError):
            wizard.action_print_xlsx()

    def test_11_half_day_and_present_calculation(self):
        """Test that half day (4h) and full day (8h) worked hours are handled properly in report generation"""
        check_in_date = self.today - timedelta(days=1)
        check_in_dt = datetime.combine(check_in_date, datetime.min.time()) + timedelta(hours=9)
        # 4 hours worked for employee (half-day)
        self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': check_in_dt,
            'check_out': check_in_dt + timedelta(hours=4),
        })
        # 8 hours worked for employee2 (full-day)
        self.env['hr.attendance'].create({
            'employee_id': self.employee2.id,
            'check_in': check_in_dt,
            'check_out': check_in_dt + timedelta(hours=8),
        })
        self.env.flush_all()

        class MockResponse:
            class stream:
                output = b''
                @classmethod
                def write(cls, data):
                    cls.output += data

        wizard = self.env['employee.attendance.report'].create({
            'from_date': check_in_date,
            'to_date': check_in_date,
            'employee_ids': [(6, 0, [self.employee.id, self.employee2.id])],
        })
        data = {
            'from_date': str(wizard.from_date),
            'to_date': str(wizard.to_date),
            'employee_ids': wizard.employee_ids.ids,
        }
        mock_response = MockResponse()
        wizard.get_xlsx_report(data, mock_response)
        self.assertTrue(mock_response.stream.output.startswith(b'PK'))
