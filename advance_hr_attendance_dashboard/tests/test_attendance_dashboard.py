# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from datetime import date, timedelta
from odoo.tools import date_utils
from odoo import fields
import pandas

class TestHrAttendanceDashboard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestHrAttendanceDashboard, cls).setUpClass()
        
        # Setup company
        cls.company = cls.env['res.company'].create({
            'name': 'Test Company',
        })
        
        # Setup employee
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'company_id': cls.company.id,
        })
        
        # Setup config settings
        cls.config = cls.env['res.config.settings'].create({
            'present': 'p',
            'absent': 'a',
        })
        cls.config.execute()
        
        # Setup leave type
        cls.leave_type = cls.env['hr.leave.type'].create({
            'name': 'Test Leave Type',
            'leave_code': 'SL',
            'color': 1,
            'requires_allocation': 'no',
        })
        
        # Setup attendance
        cls.attendance = cls.env['hr.attendance'].create({
            'employee_id': cls.employee.id,
            'check_in': fields.Datetime.now() - timedelta(days=1),
            'check_out': fields.Datetime.now() - timedelta(days=1) + timedelta(hours=8),
        })

    def test_hr_leave_type_creation(self):
        """Test if the leave type with leave_code is created successfully."""
        self.assertEqual(self.leave_type.leave_code, 'SL')

    def test_res_config_settings(self):
        """Test if the default present and absent marks are configured properly."""
        config_present = self.env['ir.config_parameter'].sudo().get_param('advance_hr_attendance_dashboard.present')
        config_absent = self.env['ir.config_parameter'].sudo().get_param('advance_hr_attendance_dashboard.absent')
        self.assertEqual(config_present, 'p')
        self.assertEqual(config_absent, 'a')

    def test_get_employee_leave_data_last_15_days(self):
        """Test get_employee_leave_data method with last_15_days option."""
        # Using a mock request might be tricky without mocking, but since we are calling it directly 
        # in a test environment where we can bypass the cookie check by mocking or patching
        
        # Mocking the request to provide a cookie 'cids'
        from unittest import mock
        with mock.patch('odoo.http.request') as mock_request:
            mock_request.httprequest.cookies.get.return_value = str(self.company.id)
            
            # Since test is running under TransactionCase without http request context, 
            # we need to be careful with http.request
            
            result = self.employee.get_employee_leave_data('last_15_days')
            self.assertIn('employee_data', result)
            self.assertIn('filtered_duration_dates', result)
            
            # Check if employee data is populated
            employee_data = [emp for emp in result['employee_data'] if emp['id'] == self.employee.id]
            self.assertTrue(len(employee_data) > 0)
            
            self.assertEqual(employee_data[0]['name'], self.employee.name)
            self.assertTrue(len(employee_data[0]['leave_data']) > 0)

    def test_get_employee_leave_data_this_week(self):
        """Test get_employee_leave_data method with this_week option."""
        from unittest import mock
        with mock.patch('odoo.http.request') as mock_request:
            mock_request.httprequest.cookies.get.return_value = str(self.company.id)
            result = self.employee.get_employee_leave_data('this_week')
            self.assertIn('employee_data', result)
            self.assertIn('filtered_duration_dates', result)

    def test_get_employee_leave_data_this_month(self):
        """Test get_employee_leave_data method with this_month option."""
        from unittest import mock
        with mock.patch('odoo.http.request') as mock_request:
            mock_request.httprequest.cookies.get.return_value = str(self.company.id)
            result = self.employee.get_employee_leave_data('this_month')
            self.assertIn('employee_data', result)
            self.assertIn('filtered_duration_dates', result)
