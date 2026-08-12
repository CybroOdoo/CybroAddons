# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError


@tagged('post_install', '-at_install')
class TestHikvisionDevice(TransactionCase):
    """Test suite for Hikvision Biometric Device management model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.device = cls.env['hikvision.device'].create({
            'name': 'Test Device Main Entrance',
            'ip_address': '192.168.1.200',
            'username': 'admin',
            'password': 'password123',
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'John Doe',
            'hikvision_number': '1001',
            'work_email': 'john.doe@example.com',
        })

    def test_get_api_config(self):
        """Test API endpoint, auth, and header generation."""
        url, auth, headers = self.device._get_api_config("/ISAPI/System/deviceInfo")
        self.assertEqual(url, "http://192.168.1.200/ISAPI/System/deviceInfo")
        self.assertEqual(headers, {"Content-Type": "application/json"})
        self.assertEqual(auth.username, 'admin')
        self.assertEqual(auth.password, 'password123')

    @patch('requests.get')
    def test_test_connection_success(self, mock_get):
        """Test successful connection to Hikvision device."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <DeviceInfo xmlns="http://www.hikvision.com/ver10/XMLSchema" version="2.0">
            <deviceName>Front Gate</deviceName>
            <deviceID>DEV-001</deviceID>
            <model>DS-K1T804MF</model>
            <serialNumber>DS-K1T804MF123456789</serialNumber>
            <macAddress>00:11:22:33:44:55</macAddress>
        </DeviceInfo>"""
        mock_get.return_value = mock_response

        res = self.device.test_connection()
        self.assertEqual(self.device.device_name, 'Front Gate')
        self.assertEqual(self.device.device_id, 'DEV-001')
        self.assertEqual(self.device.device_model, 'DS-K1T804MF')
        self.assertEqual(self.device.device_serial_no, 'DS-K1T804MF123456789')
        self.assertEqual(self.device.device_mac_address, '00:11:22:33:44:55')
        self.assertEqual(res['type'], 'ir.actions.client')

    @patch('requests.get')
    def test_test_connection_failure(self, mock_get):
        """Test connection failure when device is unreachable."""
        mock_get.side_effect = Exception("Connection refused")
        with self.assertRaises(ValidationError):
            self.device.test_connection()

    @patch('requests.post')
    def test_fetch_attendance(self, mock_post):
        """Test fetching attendance records from Hikvision device."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'AcsEvent': {
                'totalMatches': 1,
                'InfoList': [
                    {
                        'employeeNoString': '1001',
                        'time': '2026-08-01T08:00:00+00:00',
                        'attendanceStatus': 'checkIn',
                        'minor': 38,
                    }
                ]
            }
        }
        mock_post.return_value = mock_response

        events = self.device.fetch_attendance(start_date=date(2026, 8, 1), end_date=date(2026, 8, 1))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['employeeNoString'], '1001')

    @patch('requests.post')
    def test_fetch_employees(self, mock_post):
        """Test fetching employees from device and syncing with Odoo."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'UserInfoSearch': {
                'UserInfo': [
                    {'employeeNo': '1001', 'name': 'John Doe Updated'},
                    {'employeeNo': '1002', 'name': 'Jane Smith'}
                ]
            }
        }
        mock_post.return_value = mock_response

        res = self.device.fetch_employees()
        self.assertEqual(self.employee.name, 'John Doe Updated')
        new_emp = self.env['hr.employee'].search([('hikvision_number', '=', '1002')], limit=1)
        self.assertTrue(new_emp.exists())
        self.assertEqual(new_emp.name, 'Jane Smith')
        self.assertEqual(res['res_model'], 'hr.employee')

    @patch('hikvision.device.HikvisionDevice.fetch_attendance')
    def test_fetch_logs(self, mock_fetch):
        """Test fetching and creating audit logs."""
        mock_fetch.return_value = [
            {
                'employeeNoString': '1001',
                'time': '2026-08-01T09:00:00+00:00',
                'attendanceStatus': 'checkIn',
                'minor': 38
            }
        ]
        self.device.fetch_logs()
        log = self.env['hikvision.logs'].search([('employee_id', '=', self.employee.id)], limit=1)
        self.assertTrue(log.exists())
        self.assertEqual(log.punch_type, '0')  # checkIn -> 0
        self.assertEqual(log.attendance_type, '1')  # 38 -> 1

    @patch('requests.put')
    def test_set_time_success(self, mock_put):
        """Test setting device time successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        res = self.device.set_time()
        self.assertEqual(res['tag'], 'display_notification')

    @patch('requests.put')
    def test_set_time_failure(self, mock_put):
        """Test failure when setting device time."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_put.return_value = mock_response

        with self.assertRaises(UserError):
            self.device.set_time()

    def test_get_next_hikvision_employee_no(self):
        """Test auto-generating the next Hikvision employee number."""
        next_no = self.device._get_next_hikvision_employee_no()
        self.assertEqual(next_no, 1002)

    @patch('requests.post')
    def test_create_hikvision_user_success(self, mock_post):
        """Test creating user on Hikvision device."""
        emp_new = self.env['hr.employee'].create({'name': 'Alice Smith'})
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        res = self.device.create_hikvision_user(emp_new)
        self.assertEqual(emp_new.hikvision_number, '1002')
        self.assertEqual(res['tag'], 'display_notification')

    @patch('requests.put')
    def test_update_hikvision_user_success(self, mock_put):
        """Test updating user on Hikvision device."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        res = self.device.update_hikvision_user(self.employee)
        self.assertEqual(res['tag'], 'display_notification')

    @patch('requests.put')
    def test_archive_hikvision_user(self, mock_put):
        """Test deleting user from device and archiving in Odoo."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        res = self.device.archive_hikvision_user(self.employee)
        self.assertFalse(self.employee.active)
        self.assertEqual(res['tag'], 'display_notification')

    @patch('hikvision.device.HikvisionDevice.fetch_attendance')
    @patch('hikvision.device.HikvisionDevice.fetch_employees')
    def test_job_download_attendance(self, mock_fetch_emp, mock_fetch_att):
        """Test job processing of attendance download and pairing check-in/out."""
        # Ensure employee create_date is prior to event time
        self.employee.write({'create_date': datetime(2020, 1, 1)})
        mock_fetch_att.return_value = [
            {
                'employeeNoString': '1001',
                'time': '2026-08-01T08:00:00+00:00',
                'attendanceStatus': 'checkIn'
            },
            {
                'employeeNoString': '1001',
                'time': '2026-08-01T17:00:00+00:00',
                'attendanceStatus': 'checkOut'
            }
        ]

        result = self.device.job_download_attendance(self.device.id)
        self.assertIn("completed successfully", result)

        att = self.env['hr.attendance'].search([('employee_id', '=', self.employee.id)], limit=1)
        self.assertTrue(att.exists())
        self.assertEqual(att.check_in, datetime(2026, 8, 1, 8, 0, 0))
        self.assertEqual(att.check_out, datetime(2026, 8, 1, 17, 0, 0))

    @patch('hikvision.device.HikvisionDevice.fetch_and_create_attendance')
    def test_cron_download_attendance_all_devices(self, mock_fetch):
        """Test daily cron job calling attendance sync across devices."""
        res = self.env['hikvision.device'].cron_download_attendance_all_devices()
        self.assertTrue(res)
        mock_fetch.assert_called()
