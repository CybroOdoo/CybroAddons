# -*- coding: utf-8 -*-

from datetime import datetime
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.hr_zk_attendance.models import (
    biometric_device_details as biometric_module,
)


class FakeUser:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name


class FakePunch:
    def __init__(self, user_id, punch, timestamp):
        self.user_id = user_id
        self.punch = punch
        self.timestamp = timestamp
        self.status = 1


class FakeConnection:
    def __init__(self, users=None, attendance=None):
        self.users = users or []
        self.attendance = attendance or []
        self.enabled = False
        self.disabled = False
        self.cleared = False
        self.disconnected = False
        self.restarted = False
        self.set_time_value = False

    def set_time(self, value):
        self.set_time_value = value

    def enable_device(self):
        self.enabled = True

    def disable_device(self):
        self.disabled = True

    def get_users(self):
        return self.users

    def get_attendance(self):
        return self.attendance

    def clear_attendance(self):
        self.cleared = True

    def disconnect(self):
        self.disconnected = True

    def restart(self):
        self.restarted = True


class FakeZK:
    connection = FakeConnection()
    attendance = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def connect(self):
        return self.connection

    def get_attendance(self):
        return self.attendance


class TestBiometricDeviceDetails(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.partner_id.tz = 'UTC'
        cls.address = cls.env['res.partner'].create({
            'name': 'Biometric Office',
        })
        cls.device = cls.env['biometric.device.details'].create({
            'name': 'Test Device',
            'device_ip': '127.0.0.1',
            'port_number': 4370,
            'address_id': cls.address.id,
        })

    def test_device_connect_returns_connection(self):
        connection = FakeConnection()
        zk = FakeZK()
        zk.connection = connection

        self.assertEqual(self.device.device_connect(zk), connection)

    def test_device_connect_returns_false_on_connection_error(self):
        class FailingZK:
            def connect(self):
                raise RuntimeError('Connection failed')

        self.assertFalse(self.device.device_connect(FailingZK()))

    def test_action_test_connection_returns_success_notification(self):
        with patch.object(biometric_module, 'ZK', FakeZK, create=True):
            action = self.device.action_test_connection()

        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'success')
        self.assertEqual(action['params']['message'], 'Successfully Connected')

    def test_action_test_connection_raises_validation_error_on_failure(self):
        class FailingZK(FakeZK):
            def connect(self):
                raise RuntimeError('Device unreachable')

        with patch.object(biometric_module, 'ZK', FailingZK, create=True):
            with self.assertRaises(ValidationError):
                self.device.action_test_connection()

    def test_action_set_timezone_updates_connected_device(self):
        connection = FakeConnection()

        with patch.object(type(self.device), 'device_connect', autospec=True, return_value=connection), \
             patch.object(biometric_module, 'ZK', FakeZK, create=True):
            action = self.device.with_context(tz='Asia/Kolkata').action_set_timezone()

        self.assertEqual(action['tag'], 'display_notification')
        self.assertTrue(connection.set_time_value)

    def test_action_set_timezone_raises_user_error_without_connection(self):
        with patch.object(type(self.device), 'device_connect', autospec=True, return_value=False), \
             patch.object(biometric_module, 'ZK', FakeZK, create=True):
            with self.assertRaises(UserError):
                self.device.action_set_timezone()

    def test_action_clear_attendance_clears_device_and_local_logs(self):
        employee = self.env['hr.employee'].create({
            'name': 'Biometric Employee',
        })
        self.env['zk.machine.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2026-05-04 09:00:00',
            'device_id_num': '1001',
            'attendance_type': '1',
            'punch_type': '0',
            'punching_time': '2026-05-04 09:00:00',
            'address_id': self.address.id,
        })
        connection = FakeConnection()
        fake_zk = type('ClearAttendanceZK', (FakeZK,), {
            'connection': connection,
            'attendance': [object()],
        })

        with patch.object(type(self.device), 'device_connect', autospec=True, return_value=connection), \
             patch.object(biometric_module, 'ZK', fake_zk, create=True):
            self.device.action_clear_attendance()

        self.assertTrue(connection.enabled)
        self.assertTrue(connection.cleared)
        self.assertFalse(self.env['zk.machine.attendance'].search([]))

    def test_cron_download_calls_download_on_each_device(self):
        second_device = self.env['biometric.device.details'].create({
            'name': 'Second Device',
            'device_ip': '127.0.0.2',
            'port_number': 4370,
        })

        with patch.object(type(self.device), 'action_download_attendance', autospec=True, return_value=True) as download_mock:
            self.env['biometric.device.details'].cron_download()

        downloaded_ids = set()
        for call in download_mock.call_args_list:
            downloaded_ids.update(call.args[0].ids)
        self.assertIn(self.device.id, downloaded_ids)
        self.assertIn(second_device.id, downloaded_ids)

    def test_action_download_attendance_creates_employee_and_attendance(self):
        connection = FakeConnection(
            users=[FakeUser('1001', 'New Biometric Employee')],
            attendance=[FakePunch('1001', 0, datetime(2026, 5, 4, 9, 0, 0))],
        )

        with patch.object(type(self.device), 'device_connect', autospec=True, return_value=connection), \
             patch.object(type(self.device), 'action_set_timezone', autospec=True, return_value=True), \
             patch.object(biometric_module, 'ZK', FakeZK, create=True):
            result = self.device.action_download_attendance()

        employee = self.env['hr.employee'].search([
            ('device_id_num', '=', '1001'),
        ], limit=1)
        machine_attendance = self.env['zk.machine.attendance'].search([
            ('employee_id', '=', employee.id),
            ('punching_time', '=', '2026-05-04 09:00:00'),
        ])
        hr_attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_in', '=', '2026-05-04 09:00:00'),
        ])

        self.assertTrue(result)
        self.assertTrue(connection.disabled)
        self.assertEqual(employee.name, 'New Biometric Employee')
        self.assertEqual(machine_attendance.address_id, self.address)
        self.assertTrue(hr_attendance)

    def test_action_download_attendance_updates_open_attendance_checkout(self):
        employee = self.env['hr.employee'].create({
            'name': 'Existing Biometric Employee',
            'device_id_num': '1002',
        })
        open_attendance = self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2026-05-04 09:00:00',
        })
        connection = FakeConnection(
            users=[FakeUser('1002', employee.name)],
            attendance=[FakePunch('1002', 1, datetime(2026, 5, 4, 18, 0, 0))],
        )

        with patch.object(type(self.device), 'device_connect', autospec=True, return_value=connection), \
             patch.object(type(self.device), 'action_set_timezone', autospec=True, return_value=True), \
             patch.object(biometric_module, 'ZK', FakeZK, create=True):
            self.device.action_download_attendance()

        self.assertEqual(
            open_attendance.check_out.strftime('%Y-%m-%d %H:%M:%S'),
            '2026-05-04 18:00:00',
        )

    def test_action_download_attendance_rejects_empty_device_log(self):
        connection = FakeConnection(users=[FakeUser('1001', 'Employee')])

        with patch.object(type(self.device), 'device_connect', autospec=True, return_value=connection), \
             patch.object(type(self.device), 'action_set_timezone', autospec=True, return_value=True), \
             patch.object(biometric_module, 'ZK', FakeZK, create=True):
            with self.assertRaises(UserError):
                self.device.action_download_attendance()

    def test_action_restart_device_restarts_connection(self):
        connection = FakeConnection()

        with patch.object(type(self.device), 'device_connect', autospec=True, return_value=connection), \
             patch.object(biometric_module, 'ZK', FakeZK, create=True):
            self.device.action_restart_device()

        self.assertTrue(connection.restarted)
