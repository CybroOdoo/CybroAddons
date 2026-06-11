# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gee Paul Joby (odoo@cybrosys.com)
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
################################################################################
from datetime import date, datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestEmployeeAttendanceReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestEmployeeAttendanceReport, cls).setUpClass()
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


