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
#    GNU AFFERO PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.hr_zkteco_adms.controllers.main import ZktecoAdmsController


@tagged('post_install', '-at_install')
class TestZktecoAdms(TransactionCase):

    @classmethod
    def setUpClass(cls):
        """Set up shared test data for ZKTeco attendance test cases.
                Creates a test company reference, a ZKTeco device with its serial
                number and timezone, and an employee linked to a ZKTeco user ID.
                These records are reused across the test cases in the test class."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.device = cls.env['zkteco.device'].create({
            'name': 'Main Gate',
            'serial_number': 'TESTSN0001',
            'device_tz': 'Africa/Addis_Ababa',   # UTC+3, no DST
            'company_id': cls.company.id,
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Abebe Bekele',
            'zkteco_user_id': '17',
            'company_id': cls.company.id,
        })

    # -------------------------------------------------------------
    # Parsing
    # -------------------------------------------------------------
    def test_device_time_converted_to_utc(self):
        """Verify that device-local time is correctly converted to UTC."""
        self.assertEqual(
            self.device._device_time_to_utc('2026-03-02 08:30:00'),
            datetime(2026, 3, 2, 5, 30, 0),
        )

    def test_tz_offset_hours(self):
        """Verify that the device timezone offset is correctly calculated."""
        self.assertEqual(self.device._tz_offset_hours(), 3)

    def test_attlog_line_split_accepts_spaces(self):
        """Verify that attendance log lines can be split using tabs or spaces."""
        tabbed = self.device._split_attlog_line('17\t2026-03-02 08:30:00\t0\t1')
        spaced = self.device._split_attlog_line('17 2026-03-02 08:30:00 0 1')
        self.assertEqual(tabbed, ['17', '2026-03-02 08:30:00', '0', '1'])
        self.assertEqual(spaced, tabbed)

    def test_handshake_contains_stamps_and_timezone(self):
        """Verify that the handshake response contains the device stamps and timezone."""
        response = self.device._handshake_response()
        self.assertIn('GET OPTION FROM: TESTSN0001', response)
        self.assertIn('ATTLOGStamp=None', response)
        self.assertIn('TimeZone=3', response)

    def test_options_payload_updates_device(self):
        """Verify that device options payload correctly updates device details."""
        self.device._process_options(
            '~DeviceName=uFace800\tFWVersion=Ver 6.60 Apr 20 2020\t'
            'UserCount=42\tFPCount=80\tFaceCount=12\tTransactionCount=1500\t'
            'IPAddress=192.168.1.201'
        )
        self.assertEqual(self.device.model_name, 'uFace800')
        self.assertEqual(self.device.firmware_version, 'Ver 6.60 Apr 20 2020')
        self.assertEqual(self.device.device_user_count, 42)
        self.assertEqual(self.device.device_log_count, 1500)
        self.assertEqual(self.device.device_ip, '192.168.1.201')

    # -------------------------------------------------------------
    # Punch processing
    # -------------------------------------------------------------
    def test_attlog_creates_attendance_pair(self):
        """Verify that paired biometric punches create a complete attendance record."""
        self.device._process_attlog(
            '17\t2026-03-02 08:30:00\t0\t1\n'
            '17\t2026-03-02 17:15:00\t1\t1\n'
        )
        logs = self.env['zkteco.attendance.log'].search(
            [('device_id', '=', self.device.id)], order='punch_time')
        self.assertEqual(len(logs), 2)
        self.assertEqual(set(logs.mapped('state')), {'done'})
        attendance = logs.attendance_id
        self.assertEqual(len(attendance), 1)
        self.assertEqual(attendance.employee_id, self.employee)
        self.assertEqual(attendance.check_in, datetime(2026, 3, 2, 5, 30))
        self.assertEqual(attendance.check_out, datetime(2026, 3, 2, 14, 15))
        self.assertEqual(attendance.in_mode, 'biometric')
        self.assertEqual(attendance.out_mode, 'biometric')

    def test_status_255_alternates(self):
        """Devices that do not label punches alternate in/out."""
        self.device._process_attlog(
            '17\t2026-03-03 08:00:00\t255\t1\n'
            '17\t2026-03-03 16:00:00\t255\t1\n'
        )
        attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee.id)])
        self.assertEqual(len(attendance), 1)
        self.assertTrue(attendance.check_out)

    def test_duplicate_push_is_ignored(self):
        """Verify that duplicate attendance log pushes are ignored."""
        payload = '17\t2026-03-04 08:00:00\t0\t1\n'
        first = self.device._process_attlog(payload)
        second = self.device._process_attlog(payload)
        self.assertEqual(first, 1)
        self.assertEqual(second, 0)
        self.assertEqual(self.env['zkteco.attendance.log'].search_count([
            ('device_id', '=', self.device.id)]), 1)

    def test_unknown_pin_stays_unmapped_then_resolves(self):
        """Verify that an unknown user PIN remains unmapped until an employee is assigned."""
        self.device._process_attlog('99\t2026-03-05 08:00:00\t0\t1\n')
        log = self.env['zkteco.attendance.log'].search([
            ('device_id', '=', self.device.id), ('device_user_id', '=', '99')])
        self.assertEqual(log.state, 'unmapped')

        device_user = self.env['zkteco.device.user'].create({
            'device_id': self.device.id,
            'user_pin': '99',
            'name': 'Kebede',
        })
        other = self.env['hr.employee'].create({
            'name': 'Kebede Alemu', 'company_id': self.company.id})
        device_user.employee_id = other

        self.assertEqual(log.state, 'done')
        self.assertEqual(log.employee_id, other)
        self.assertTrue(log.attendance_id)

    def test_badge_id_is_used_as_fallback(self):
        """Verify that an employee barcode is used to map an unknown device user."""
        self.env['hr.employee'].create({
            'name': 'Selam Tesfaye',
            'barcode': 'B0042',
            'company_id': self.company.id,
        })
        self.device._process_attlog('B0042\t2026-03-06 08:00:00\t0\t1\n')
        log = self.env['zkteco.attendance.log'].search([
            ('device_user_id', '=', 'B0042')])
        self.assertEqual(log.state, 'done')
        self.assertEqual(log.employee_id.name, 'Selam Tesfaye')

    def test_checkout_without_checkin_is_flagged(self):
        """Verify that a checkout punch without an open check-in is flagged as an error."""
        self.device._process_attlog('17\t2026-03-07 17:00:00\t1\t1\n')
        log = self.env['zkteco.attendance.log'].search([
            ('punch_time', '=', datetime(2026, 3, 7, 14, 0))])
        self.assertEqual(log.state, 'error')
        self.assertTrue(log.error_message)

    def test_malformed_line_does_not_break_the_batch(self):
        """Verify that a malformed attendance line is skipped without affecting valid records."""
        count = self.device._process_attlog(
            '17\tnot-a-date\t0\t1\n'
            '17\t2026-03-08 08:00:00\t0\t1\n'
        )
        self.assertEqual(count, 1)

    # -------------------------------------------------------------
    # Device users
    # -------------------------------------------------------------
    def test_operlog_registers_and_automaps_users(self):
        """Verify that an operation log registers a device user and maps the employee."""
        count = self.device._process_operlog(
            'USER PIN=17\tName=Abebe\tPri=0\tPasswd=\tCard=123\tGrp=1\n'
            'OPLOG 4\t1\t0\t0\t2026-03-02 08:00:00\t0\n'
        )
        self.assertEqual(count, 1)
        device_user = self.env['zkteco.device.user'].search([
            ('device_id', '=', self.device.id), ('user_pin', '=', '17')])
        self.assertEqual(device_user.name, 'Abebe')
        self.assertEqual(device_user.card, '123')
        self.assertEqual(device_user.employee_id, self.employee)

    def test_device_user_mapping_wins_over_employee_field(self):
        """Verify that the device user's employee mapping takes precedence."""
        other = self.env['hr.employee'].create({
            'name': 'Hana Girma', 'company_id': self.company.id})
        self.env['zkteco.device.user'].create({
            'device_id': self.device.id,
            'user_pin': '17',
            'employee_id': other.id,
        })
        self.device._process_attlog('17\t2026-03-09 08:00:00\t0\t1\n')
        log = self.env['zkteco.attendance.log'].search([
            ('device_user_id', '=', '17')])
        self.assertEqual(log.employee_id, other)

    # -------------------------------------------------------------
    # Commands and registration
    # -------------------------------------------------------------
    def test_commands_are_popped_once_and_in_order(self):
        """Verify that queued commands are returned once and in their creation order."""
        self.device.action_cmd_fetch_users()
        self.device.action_cmd_fetch_logs()
        first = self.device._pop_next_command()
        second = self.device._pop_next_command()
        self.assertEqual(first.command, 'DATA QUERY USERINFO')
        self.assertEqual(second.command, 'DATA QUERY ATTLOG')
        self.assertEqual(first.state, 'sent')
        self.assertFalse(self.device._pop_next_command())

    def test_reset_stamps_forces_full_reupload(self):
        """Verify that resetting the attendance stamp forces a full log re-upload."""
        self.device._process_attlog('17\t2026-03-10 08:00:00\t0\t1\n', stamp='9999')
        self.assertEqual(self.device.attlog_stamp, '9999')
        self.device.action_reset_stamps()
        self.assertEqual(self.device.attlog_stamp, 'None')
        self.assertIn('ATTLOGStamp=None', self.device._handshake_response())

    def test_registration_rejects_invalid_serial(self):
        """Verify that device registration rejects invalid serial numbers."""
        Device = self.env['zkteco.device']
        self.assertFalse(Device._get_or_register(''))
        self.assertFalse(Device._get_or_register('bad serial with spaces'))
        self.assertFalse(Device._get_or_register('x' * 100))

    def test_registration_creates_inactive_device(self):
        """Verify that a new device is created inactive and approved correctly."""
        device = self.env['zkteco.device']._get_or_register('NEWSN9999')
        self.assertTrue(device)
        self.assertFalse(device.active)
        device.action_approve()
        self.assertTrue(device.active)
        self.assertEqual(device.command_ids.command, 'DATA QUERY USERINFO')

    def test_inactive_device_refuses_commands(self):
        """Verify that an inactive device cannot queue commands."""
        device = self.env['zkteco.device']._get_or_register('NEWSN8888')
        with self.assertRaises(Exception):
            device.action_cmd_fetch_logs()

    # -------------------------------------------------------------
    # ADMS setup diagnostics
    # -------------------------------------------------------------
    def _fake_response(self, status_code=200, text='ERROR: unknown or invalid SN',
                       location=None):
        """Create a mock HTTP response for testing ZKTeco device requests.
                :param status_code: HTTP status code to assign to the mock response.
                :param text: Response body text.
                :param location: Optional value for the HTTP ``Location`` header.
                :return: Mock response object with the specified status, body, and headers."""
        response = Mock()
        response.status_code = status_code
        response.text = text
        response.headers = {'Location': location} if location else {}
        return response

    def test_diagnostics_flag_a_device_that_never_reported(self):
        """Verify that diagnostics flag a device that has never contacted Odoo."""
        with patch.object(type(self.device), '_probe_iclock',
                          return_value={'icon': '✅', 'level': 'success', 'text': 'ok'}):
            report = self.device._adms_diagnostics()
        self.assertEqual(report['level'], 'danger')
        self.assertIn('never contacted', report['lines'][0]['text'])

    def test_diagnostics_catch_the_https_redirect(self):
        """The odoo.sh failure: port 80 answers a 301 the firmware ignores."""
        self.env['ir.config_parameter'].sudo().set_param(
            'web.base.url', 'https://example.odoo.com')
        with patch('odoo.addons.hr_zkteco_adms.models.zkteco_device.requests.get',
                   return_value=self._fake_response(
                       301, '', 'https://example.odoo.com/iclock/cdata')):
            probe = self.device._probe_iclock('http://example.odoo.com')
        self.assertEqual(probe['level'], 'danger')
        self.assertIn('does not follow redirects', probe['text'])

    def test_diagnostics_warn_when_only_https_answers(self):
        """Verify that diagnostics warn when the device cannot communicate over HTTPS."""
        with patch('odoo.addons.hr_zkteco_adms.models.zkteco_device.requests.get',
                   return_value=self._fake_response()):
            probe = self.device._probe_iclock('https://example.odoo.com')
        self.assertEqual(probe['level'], 'warning')
        self.assertIn('cannot do TLS', probe['text'])

    def test_diagnostics_accept_plain_http(self):
        """Verify that diagnostics accept a successful plain HTTP connection."""
        with patch('odoo.addons.hr_zkteco_adms.models.zkteco_device.requests.get',
                   return_value=self._fake_response()):
            probe = self.device._probe_iclock('http://192.168.1.50:8069')
        self.assertEqual(probe['level'], 'success')

    def test_diagnostics_explain_a_404(self):
        """404 means routing, not a dead server - say which causes to check."""
        with patch('odoo.addons.hr_zkteco_adms.models.zkteco_device.requests.get',
                   return_value=self._fake_response(404, 'Not Found')):
            probe = self.device._probe_iclock('http://10.0.20.96:8069')
        self.assertEqual(probe['level'], 'danger')
        self.assertIn('dbfilter', probe['text'])

    def test_diagnostics_reject_a_loopback_base_url(self):
        """Verify that diagnostics reject a loopback web.base.url configuration."""
        self.env['ir.config_parameter'].sudo().set_param(
            'web.base.url', 'http://localhost:8069')
        with patch.object(type(self.device), '_probe_iclock',
                          return_value={'icon': '✅', 'level': 'success', 'text': 'ok'}):
            report = self.device._adms_diagnostics()
        self.assertEqual(report['level'], 'danger')
        self.assertTrue(any('loopback' in line['text'] for line in report['lines']))

    def test_diagnostics_tell_you_to_disable_domain_name_for_an_ip(self):
        """Verify that diagnostics instruct the user to disable domain name for an IP address."""
        self.env['ir.config_parameter'].sudo().set_param(
            'web.base.url', 'http://10.0.20.96:8069')
        with patch.object(type(self.device), '_probe_iclock',
                          return_value={'icon': '✅', 'level': 'success', 'text': 'ok'}):
            report = self.device._adms_diagnostics()
        keypad = next(line for line in report['lines'] if 'Server Address' in line['text'])
        self.assertIn('Enable Domain Name = OFF', keypad['text'])

    def test_diagnostics_report_an_unreachable_server(self):
        """Verify that diagnostics report an error when the server is unreachable."""
        with patch('odoo.addons.hr_zkteco_adms.models.zkteco_device.requests.get',
                   side_effect=OSError('connection refused')):
            probe = self.device._probe_iclock('http://192.168.1.50:8069')
        self.assertEqual(probe['level'], 'danger')
        self.assertIn('unreachable', probe['text'])

    def test_diagnostics_never_raise_from_the_button(self):
        """Verify that the ADMS diagnostics button returns a notification even if the server probe fails."""
        with patch('odoo.addons.hr_zkteco_adms.models.zkteco_device.requests.get',
                   side_effect=OSError('boom')):
            action = self.device.action_check_adms_setup()
        self.assertEqual(action['tag'], 'display_notification')

    # -------------------------------------------------------------
    # Status codes and check option
    # -------------------------------------------------------------
    def test_status_code_table_overrides_direction(self):
        """A site can redefine what a code means without patching."""
        self.env['zkteco.status.code'].create({
            'code': '0', 'name': 'Gate Exit', 'punch_type': 'out',
            'company_id': self.company.id,
        })
        self.device._process_attlog(
            '17\t2026-04-01 08:00:00\t255\t1\n'   # opens
            '17\t2026-04-01 17:00:00\t0\t1\n'     # 0 now means out
        )
        attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee.id)])
        self.assertEqual(len(attendance), 1)
        self.assertEqual(attendance.check_out, datetime(2026, 4, 1, 14, 0))

    def test_ignored_status_creates_no_attendance(self):
        """Verify that punches with an ignored status do not create attendance records."""
        self.env['zkteco.status.code'].create({
            'code': '9', 'name': 'Door Bell', 'punch_type': 'ignore',
            'company_id': self.company.id,
        })
        self.device._process_attlog('17\t2026-04-02 08:00:00\t9\t1\n')
        log = self.env['zkteco.attendance.log'].search([('status', '=', '9')])
        self.assertEqual(log.state, 'done')
        self.assertFalse(log.attendance_id)
        self.assertFalse(self.env['hr.attendance'].search_count([
            ('employee_id', '=', self.employee.id)]))

    def test_check_in_only_device_never_closes_attendance(self):
        """An entry-only reader must not be read as a check-out."""
        self.device.check_option = 'in'
        self.device._process_attlog(
            '17\t2026-04-03 08:00:00\t0\t1\n'
            '17\t2026-04-03 12:00:00\t1\t1\n'   # explicit out, forced to in
        )
        attendances = self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee.id)])
        # Second punch tried to open a second attendance while one was open;
        # hr_attendance rejects the overlap, so the log carries the reason.
        self.assertTrue(all(not a.check_out for a in attendances))
        logs = self.env['zkteco.attendance.log'].search([
            ('device_id', '=', self.device.id)])
        self.assertNotIn('done', logs.filtered(
            lambda log: log.punch_time.hour == 9).mapped('state'))

    def test_status_label_and_colour_come_from_the_table(self):
        """Verify that the status label and color are taken from the status code table."""
        self.device._process_attlog('17\t2026-04-04 08:00:00\t0\t1\n')
        log = self.env['zkteco.attendance.log'].search([
            ('punch_time', '=', datetime(2026, 4, 4, 5, 0))])
        self.assertEqual(log.status_label, 'Check In')
        self.assertEqual(log.status_color, 'success')

    # -------------------------------------------------------------
    # Connection modes
    # -------------------------------------------------------------
    def test_adms_device_requires_a_serial(self):
        """Verify that an ADMS device cannot be created without a serial number."""
        with self.assertRaises(ValidationError):
            self.env['zkteco.device'].create({
                'name': 'No Serial', 'connection_mode': 'adms',
            })

    def test_tcp_device_requires_an_ip(self):
        """Verify that a Direct IP device cannot be created without an IP address."""
        with self.assertRaises(ValidationError):
            self.env['zkteco.device'].create({
                'name': 'No IP', 'connection_mode': 'tcp',
            })

    def test_tcp_device_needs_no_serial(self):
        """Verify that a Direct IP device can be created without a serial number."""
        device = self.env['zkteco.device'].create({
            'name': 'Gate 2', 'connection_mode': 'tcp',
            'ip_address': '192.168.1.201',
        })
        self.assertFalse(device.serial_number)
        self.assertEqual(device.port, 4370)

    def test_tcp_device_refuses_the_adms_command_queue(self):
        """Verify that a Direct IP device cannot use the ADMS command queue."""
        device = self.env['zkteco.device'].create({
            'name': 'Gate 3', 'connection_mode': 'tcp',
            'ip_address': '192.168.1.202',
        })
        with self.assertRaises(UserError):
            device.action_cmd_fetch_logs()

    def test_adms_device_refuses_tcp_actions(self):
        """Verify that an ADMS device cannot perform Direct IP actions."""
        with self.assertRaises(UserError):
            self.device.action_test_connection()

    # -------------------------------------------------------------
    # Wizards
    # -------------------------------------------------------------
    def test_fetch_wizard_queues_a_dated_range_for_adms(self):
        """Verify that the fetch wizard queues an ADMS attendance command for the selected date range."""
        wizard = self.env['zkteco.fetch.logs.wizard'].create({
            'device_ids': [(6, 0, self.device.ids)],
            'date_from': '2026-05-01',
            'date_to': '2026-05-02',
        })
        wizard.action_fetch()
        command = self.env['zkteco.device.command'].search([
            ('device_id', '=', self.device.id)], order='id desc', limit=1)
        self.assertIn('DATA QUERY ATTLOG', command.command)
        # Window is expressed in the device's own clock, not UTC.
        self.assertIn('StartTime=2026-05-01 00:00:00', command.command)
        self.assertIn('EndTime=2026-05-02 23:59:59', command.command)

    def test_fetch_wizard_rejects_a_backwards_range(self):
        """Verify that the fetch wizard rejects a date range where the end date precedes the start date."""
        with self.assertRaises(UserError):
            self.env['zkteco.fetch.logs.wizard'].create({
                'device_ids': [(6, 0, self.device.ids)],
                'date_from': '2026-05-10',
                'date_to': '2026-05-01',
            })

    def test_export_wizard_creates_and_queues_users(self):
        """Verify that the export wizard creates device users and queues update commands."""
        wizard = self.env['zkteco.export.employees.wizard'].create({
            'device_id': self.device.id,
            'employee_ids': [(6, 0, self.employee.ids)],
        })
        wizard.action_export()
        device_user = self.env['zkteco.device.user'].search([
            ('device_id', '=', self.device.id), ('user_pin', '=', '17')])
        self.assertEqual(device_user.employee_id, self.employee)
        command = self.env['zkteco.device.command'].search([
            ('device_id', '=', self.device.id)], order='id desc', limit=1)
        self.assertIn('DATA UPDATE USERINFO PIN=17', command.command)

    def test_export_wizard_reports_employees_without_a_pin(self):
        """Verify that the export wizard rejects employees without a ZKTeco user PIN."""
        nameless = self.env['hr.employee'].create({
            'name': 'No Pin', 'company_id': self.company.id})
        wizard = self.env['zkteco.export.employees.wizard'].create({
            'device_id': self.device.id,
            'employee_ids': [(6, 0, nameless.ids)],
        })
        with self.assertRaises(UserError):
            wizard.action_export()

    # -------------------------------------------------------------
    # Employee side
    # -------------------------------------------------------------
    def test_employee_sees_its_device_registrations(self):
        """Verify that the employee displays its linked device registrations and biometric template count."""
        self.env['zkteco.device.user'].create({
            'device_id': self.device.id,
            'user_pin': '17',
            'employee_id': self.employee.id,
        })
        self.assertEqual(self.employee.zkteco_device_count, 1)
        self.assertEqual(self.employee.zkteco_template_count, 0)

    # -------------------------------------------------------------
    # Smart buttons and device views
    # -------------------------------------------------------------
    def test_device_smart_button_views(self):
        """Verify window actions returned by device smart buttons."""
        self.assertEqual(self.device.action_view_logs()['res_model'], 'zkteco.attendance.log')
        self.assertEqual(self.device.action_view_users()['res_model'], 'zkteco.device.user')
        self.assertEqual(self.device.action_view_templates()['res_model'], 'zkteco.biometric.template')
        self.assertEqual(self.device.action_view_commands()['res_model'], 'zkteco.device.command')

    def test_device_adms_commands(self):
        """Verify queuing of ADMS commands (info, clear logs, reboot, sync time)."""
        self.device.action_cmd_device_info()
        self.device.action_cmd_clear_attlog()
        self.device.action_cmd_reboot()
        self.device.action_cmd_sync_time()
        commands = self.env['zkteco.device.command'].search([
            ('device_id', '=', self.device.id), ('state', '=', 'pending')
        ]).mapped('command')
        self.assertTrue(any('INFO' in cmd for cmd in commands))
        self.assertTrue(any('CLEAR LOG' in cmd for cmd in commands))
        self.assertTrue(any('REBOOT' in cmd for cmd in commands))
        self.assertTrue(any('SET OPTION DateTime=' in cmd for cmd in commands))

    def test_device_is_online_compute_and_search(self):
        """Verify computation and search for is_online."""
        self.device.write({'last_seen': fields.Datetime.now()})
        self.assertTrue(self.device.is_online)
        domain_on = self.device._search_is_online('=', True)
        self.assertEqual(domain_on[0][0], 'last_seen')
        self.assertEqual(domain_on[0][1], '>=')

        self.device.write({'last_seen': fields.Datetime.now() - timedelta(hours=2)})
        self.assertFalse(self.device.is_online)
        domain_off = self.device._search_is_online('=', False)
        self.assertEqual(domain_off[0], '|')

    def test_device_offline_cron(self):
        """Verify offline cron logs message when a device goes offline."""
        self.device.last_seen = fields.Datetime.now() - timedelta(hours=2)
        self.env['zkteco.device']._cron_check_offline()
        messages = self.env['mail.message'].search([
            ('model', '=', 'zkteco.device'), ('res_id', '=', self.device.id),
            ('body', 'like', 'ZKTECO_OFFLINE_NOTICE')
        ])
        self.assertTrue(messages)

    def test_device_user_features(self):
        """Verify user auto_map, view punches, display label, and push/delete."""
        user = self.env['zkteco.device.user'].create({
            'device_id': self.device.id,
            'user_pin': '888',
            'name': 'Test User 888',
        })
        self.assertEqual(user.display_label, '888 - Test User 888')
        emp = self.env['hr.employee'].create({
            'name': 'Employee 888',
            'zkteco_user_id': '888',
            'company_id': self.company.id,
        })
        user.action_auto_map()
        self.assertEqual(user.employee_id, emp)
        action = user.action_view_punches()
        self.assertEqual(action['res_model'], 'zkteco.attendance.log')

        user.action_push_to_device()
        user.action_delete_from_device()
        commands = self.env['zkteco.device.command'].search([
            ('device_id', '=', self.device.id)
        ]).mapped('command')
        self.assertTrue(any('DATA UPDATE USERINFO' in cmd for cmd in commands))
        self.assertTrue(any('DATA DELETE USERINFO' in cmd for cmd in commands))

    def test_attendance_log_features(self):
        """Verify attendance log actions and cron reprocessing."""
        log = self.env['zkteco.attendance.log'].create({
            'device_id': self.device.id,
            'device_user_id': '17',
            'punch_time': datetime(2026, 3, 2, 8, 30, 0),
            'status': '0',
            'state': 'pending',
        })
        log.action_process()
        self.assertEqual(log.state, 'done')
        self.assertTrue(log.attendance_id)

        log2 = self.env['zkteco.attendance.log'].create({
            'device_id': self.device.id,
            'device_user_id': '17',
            'punch_time': datetime(2026, 3, 2, 17, 30, 0),
            'status': '1',
            'state': 'pending',
        })
        self.env['zkteco.attendance.log']._cron_process_pending()
        self.assertEqual(log2.state, 'done')

    def test_fetch_wizard_direct_ip(self):
        """Verify fetch wizard handles Direct IP devices."""
        tcp_dev = self.env['zkteco.device'].create({
            'name': 'Direct TCP Dev',
            'connection_mode': 'tcp',
            'ip_address': '192.168.1.105',
            'company_id': self.company.id,
        })
        wizard = self.env['zkteco.fetch.logs.wizard'].create({
            'device_ids': [(6, 0, tcp_dev.ids)],
            'date_from': '2026-05-01',
            'date_to': '2026-05-02',
        })
        with patch.object(type(tcp_dev), '_pull_attendance', return_value=5) as mock_pull:
            wizard.action_fetch()
            mock_pull.assert_called_once()


@tagged('post_install', '-at_install')
class TestZktecoController(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.device = cls.env['zkteco.device'].create({
            'name': 'Controller Gate',
            'serial_number': 'CTRLSN0001',
            'device_tz': 'Africa/Addis_Ababa',
            'company_id': cls.company.id,
            'active': True,
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Ctrl Abebe',
            'zkteco_user_id': '101',
            'company_id': cls.company.id,
        })
        cls.controller = ZktecoAdmsController()

    def _mock_request(self, method='GET', raw_body=b'', form=None):
        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.httprequest.method = method
        mock_req.httprequest.get_data.return_value = raw_body
        mock_req.httprequest.form = form or {}
        mock_req.make_response.side_effect = lambda body, headers: body
        return mock_req

    def _text(self, res):
        if hasattr(res, 'get_data'):
            return res.get_data(as_text=True)
        return str(res)

    def test_cdata_get_handshake(self):
        """GET /iclock/cdata returns device handshake config."""
        mock_req = self._mock_request(method='GET')
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            res = self.controller.iclock_cdata(SN=self.device.serial_number, options='all')
        self.assertIn('GET OPTION FROM: CTRLSN0001', self._text(res))
        self.assertTrue(self.device.last_seen)

    def test_cdata_unknown_serial(self):
        """GET/POST /iclock/cdata with unknown/invalid serial returns error."""
        mock_req = self._mock_request(method='GET')
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            res = self.controller.iclock_cdata(SN='invalid serial spaces')
        self.assertEqual(self._text(res), 'ERROR: unknown or invalid SN')

    def test_cdata_inactive_device(self):
        """GET /iclock/cdata with inactive device returns OK without processing."""
        inactive = self.env['zkteco.device'].create({
            'name': 'Pending Dev',
            'serial_number': 'PENDING0001',
            'active': False,
        })
        mock_req = self._mock_request(method='GET')
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            res = self.controller.iclock_cdata(SN=inactive.serial_number)
        self.assertEqual(self._text(res), 'OK')

    def test_cdata_post_attlog(self):
        """POST /iclock/cdata?table=ATTLOG processes punches."""
        body = b'101\t2026-03-02 08:30:00\t0\t1\n'
        mock_req = self._mock_request(method='POST', raw_body=body)
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            res = self.controller.iclock_cdata(SN=self.device.serial_number, table='ATTLOG')
        self.assertEqual(self._text(res), 'OK: 1')

    def test_cdata_post_operlog(self):
        """POST /iclock/cdata?table=OPERLOG processes users."""
        body = b'USER PIN=101\tName=Ctrl Abebe\tPri=0\tPasswd=\tCard=999\tGrp=1\n'
        mock_req = self._mock_request(method='POST', raw_body=body)
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            res = self.controller.iclock_cdata(SN=self.device.serial_number, table='OPERLOG')
        self.assertEqual(self._text(res), 'OK: 1')

    def test_cdata_post_options(self):
        """POST /iclock/cdata?table=OPTIONS updates device info."""
        body = b'~DeviceName=uFace800\tFWVersion=Ver 6.60'
        mock_req = self._mock_request(method='POST', raw_body=body)
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            res = self.controller.iclock_cdata(SN=self.device.serial_number, table='OPTIONS')
        self.assertEqual(self._text(res), 'OK: 2')
        self.assertEqual(self.device.model_name, 'uFace800')

    def test_cdata_post_unhandled_table(self):
        """POST /iclock/cdata with unhandled table returns OK: 0."""
        mock_req = self._mock_request(method='POST', raw_body=b'ignored')
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            res = self.controller.iclock_cdata(SN=self.device.serial_number, table='ATTPHOTO')
        self.assertEqual(self._text(res), 'OK: 0')

    def test_cdata_post_exception_returns_ok(self):
        """POST /iclock/cdata catches exceptions and returns OK: 0."""
        mock_req = self._mock_request(method='POST', raw_body=b'bad')
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            with patch.object(type(self.device), '_process_attlog', side_effect=Exception('boom')):
                res = self.controller.iclock_cdata(SN=self.device.serial_number, table='ATTLOG')
        self.assertEqual(self._text(res), 'OK: 0')

    def test_cdata_form_payload_fallback(self):
        """When get_data() is empty, rebuild body from form."""
        mock_form = Mock()
        mock_form.items.return_value = [('101 2026-03-02 08:30:00 0 1', '')]
        mock_req = self._mock_request(method='POST', raw_body=b'', form=mock_form)
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            res = self.controller.iclock_cdata(SN=self.device.serial_number, table='ATTLOG')
        self.assertIn('OK:', self._text(res))

    def test_getrequest_commands(self):
        """GET /iclock/getrequest pops queued commands."""
        self.device.action_cmd_fetch_users()
        mock_req = self._mock_request(method='GET')
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            res = self.controller.iclock_getrequest(SN=self.device.serial_number, INFO='Firmware123')
        text = self._text(res)
        self.assertTrue(text.startswith('C:'))
        self.assertIn('DATA QUERY USERINFO', text)
        self.assertEqual(self.device.firmware_version, 'Firmware123')

        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            res_empty = self.controller.iclock_getrequest(SN=self.device.serial_number)
        self.assertEqual(self._text(res_empty), 'OK')

    def test_devicecmd_updates_command_state(self):
        """POST /iclock/devicecmd updates command return status."""
        cmd = self.env['zkteco.device.command'].create({
            'device_id': self.device.id,
            'command': 'REBOOT',
            'state': 'sent',
        })
        body = f'ID={cmd.id}&Return=0&CMD=REBOOT\n'.encode()
        mock_req = self._mock_request(method='POST', raw_body=body)
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            res = self.controller.iclock_devicecmd(SN=self.device.serial_number)
        self.assertEqual(self._text(res), 'OK')
        self.assertEqual(cmd.state, 'done')
        self.assertEqual(cmd.return_code, '0')

        cmd_err = self.env['zkteco.device.command'].create({
            'device_id': self.device.id,
            'command': 'CLEAR LOG',
            'state': 'sent',
        })
        body_err = f'ID={cmd_err.id}&Return=-1&CMD=CLEAR LOG\n'.encode()
        mock_req_err = self._mock_request(method='POST', raw_body=body_err)
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req_err):
            self.controller.iclock_devicecmd(SN=self.device.serial_number)
        self.assertEqual(cmd_err.state, 'error')

    def test_devicecmd_rejects_missing_or_mismatched_device(self):
        """Anonymous or mismatched SN cannot mark commands as done."""
        cmd = self.env['zkteco.device.command'].create({
            'device_id': self.device.id,
            'command': 'INFO',
            'state': 'sent',
        })
        body = f'ID={cmd.id}&Return=0&CMD=INFO\n'.encode()

        # 1. No SN provided
        mock_req = self._mock_request(method='POST', raw_body=body)
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            res = self.controller.iclock_devicecmd()
        self.assertEqual(self._text(res), 'OK')
        self.assertEqual(cmd.state, 'sent')

        # 2. Mismatched SN from another device
        other_dev = self.env['zkteco.device'].create({
            'name': 'Other Device',
            'serial_number': 'OTHERDEV0001',
            'active': True,
        })
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            self.controller.iclock_devicecmd(SN=other_dev.serial_number)
        self.assertEqual(cmd.state, 'sent')

        # 3. Inactive device SN
        inactive_dev = self.env['zkteco.device'].create({
            'name': 'Inactive Dev',
            'serial_number': 'INACTIVEDEV01',
            'active': False,
        })
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            self.controller.iclock_devicecmd(SN=inactive_dev.serial_number)
        self.assertEqual(cmd.state, 'sent')

    def test_misc_endpoints(self):
        """Auxiliary endpoints return OK and update last_seen."""
        mock_req = self._mock_request(method='GET')
        with patch('odoo.addons.hr_zkteco_adms.controllers.main.request', mock_req):
            res = self.controller.iclock_misc(SN=self.device.serial_number)
        self.assertEqual(self._text(res), 'OK')


@tagged('post_install', '-at_install')
class TestZktecoTcp(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.device = cls.env['zkteco.device'].create({
            'name': 'TCP Direct Gate',
            'connection_mode': 'tcp',
            'ip_address': '192.168.1.100',
            'port': 4370,
            'device_tz': 'Africa/Addis_Ababa',
            'company_id': cls.company.id,
            'active': True,
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'TCP Abebe',
            'zkteco_user_id': '201',
            'company_id': cls.company.id,
        })

    def _mock_zk_connection(self):
        conn = Mock()
        conn.users = 3
        conn.records = 15
        conn.fingers = 2
        conn.get_serialnumber.return_value = 'TCPSERIAL01'
        conn.get_firmware_version.return_value = 'Ver 8.0.1'
        conn.get_device_name.return_value = 'iClock580'
        conn.get_time.return_value = datetime(2026, 3, 2, 8, 30, 0)

        user_mock = Mock()
        user_mock.user_id = '201'
        user_mock.name = 'TCP Abebe'
        user_mock.card = 12345
        user_mock.privilege = 0
        user_mock.uid = 1
        conn.get_users.return_value = [user_mock]

        att_mock = Mock()
        att_mock.user_id = '201'
        att_mock.timestamp = datetime(2026, 3, 2, 8, 30, 0)
        att_mock.punch = 0
        att_mock.status = 1
        conn.get_attendance.return_value = [att_mock]

        tpl_mock = Mock()
        tpl_mock.uid = 1
        tpl_mock.fid = 0
        tpl_mock.template = b'raw_fingerprint_blob'
        tpl_mock.valid = 1
        conn.get_templates.return_value = [tpl_mock]
        return conn

    def test_tcp_session_lifecycle(self):
        """Test _zk_session connect, disable, enable, disconnect."""
        conn = self._mock_zk_connection()
        mock_zk_cls = Mock()
        mock_zk_inst = mock_zk_cls.return_value
        mock_zk_inst.connect.return_value = conn

        with patch('odoo.addons.hr_zkteco_adms.models.zkteco_device_tcp.ZK', mock_zk_cls):
            with self.device._zk_session(disable_device=True) as session:
                self.assertEqual(session, conn)
            conn.disable_device.assert_called_once()
            conn.enable_device.assert_called_once()
            conn.disconnect.assert_called_once()

    def test_tcp_session_failure_raises_user_error(self):
        """Failed connection raises UserError."""
        mock_zk_cls = Mock()
        mock_zk_inst = mock_zk_cls.return_value
        mock_zk_inst.connect.side_effect = Exception('connection timed out')

        with patch('odoo.addons.hr_zkteco_adms.models.zkteco_device_tcp.ZK', mock_zk_cls):
            with self.assertRaises(UserError):
                with self.device._zk_session():
                    pass

    def test_tcp_action_test_connection(self):
        """action_test_connection updates device parameters."""
        conn = self._mock_zk_connection()
        with patch.object(type(self.device), '_zk_session') as mock_sess:
            mock_sess.return_value.__enter__.return_value = conn
            action = self.device.action_test_connection()
        self.assertEqual(action['params']['type'], 'success')
        self.assertEqual(self.device.serial_number, 'TCPSERIAL01')
        self.assertEqual(self.device.firmware_version, 'Ver 8.0.1')
        self.assertEqual(self.device.device_user_count, 3)
        self.assertEqual(self.device.device_log_count, 15)

    def test_tcp_pull_users(self):
        """action_pull_users fetches users and updates device users."""
        conn = self._mock_zk_connection()
        with patch.object(type(self.device), '_zk_session') as mock_sess:
            mock_sess.return_value.__enter__.return_value = conn
            self.device.action_pull_users()
        user = self.env['zkteco.device.user'].search([
            ('device_id', '=', self.device.id), ('user_pin', '=', '201')])
        self.assertTrue(user)
        self.assertEqual(user.employee_id, self.employee)

    def test_tcp_pull_attendance(self):
        """action_pull_attendance fetches attendance records."""
        conn = self._mock_zk_connection()
        with patch.object(type(self.device), '_zk_session') as mock_sess:
            mock_sess.return_value.__enter__.return_value = conn
            self.device.action_pull_attendance()
        logs = self.env['zkteco.attendance.log'].search([
            ('device_id', '=', self.device.id), ('device_user_id', '=', '201')])
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs.state, 'done')

    def test_tcp_pull_biometrics(self):
        """action_pull_biometrics imports templates and cards."""
        conn = self._mock_zk_connection()
        with patch.object(type(self.device), '_zk_session') as mock_sess:
            mock_sess.return_value.__enter__.return_value = conn
            self.device.action_pull_biometrics()
        template = self.env['zkteco.biometric.template'].search([
            ('device_id', '=', self.device.id), ('template_type', '=', 'finger')])
        self.assertTrue(template)
        card_tpl = self.env['zkteco.biometric.template'].search([
            ('device_id', '=', self.device.id), ('template_type', '=', 'card')])
        self.assertTrue(card_tpl)

    def test_tcp_sync_now(self):
        """action_sync_now runs both pull_users and pull_attendance."""
        conn = self._mock_zk_connection()
        with patch.object(type(self.device), '_zk_session') as mock_sess:
            mock_sess.return_value.__enter__.return_value = conn
            action = self.device.action_sync_now()
        self.assertEqual(action['params']['type'], 'success')

    def test_tcp_sync_time_and_actions(self):
        """Test sync time, reboot, and clear attendance logs."""
        conn = self._mock_zk_connection()
        with patch.object(type(self.device), '_zk_session') as mock_sess:
            mock_sess.return_value.__enter__.return_value = conn
            self.device.action_tcp_sync_time()
            conn.set_time.assert_called_once()

            self.device.action_tcp_reboot()
            conn.restart.assert_called_once()

            self.device.action_tcp_clear_attendance()
            conn.clear_attendance.assert_called_once()

    def test_tcp_user_push_and_delete(self):
        """Test setting and deleting user on TCP device."""
        conn = self._mock_zk_connection()
        user = self.env['zkteco.device.user'].create({
            'device_id': self.device.id,
            'user_pin': '201',
            'employee_id': self.employee.id,
            'card': '12345',
        })
        with patch.object(type(self.device), '_zk_session') as mock_sess:
            mock_sess.return_value.__enter__.return_value = conn
            user.action_push_to_device()
            conn.set_user.assert_called_once()

            user.action_delete_from_device()
            conn.delete_user.assert_called_once()

    def test_cron_pull_tcp_devices(self):
        """Cron pulls attendance for auto_pull tcp devices."""
        self.device.auto_pull = True
        conn = self._mock_zk_connection()
        with patch.object(type(self.device), '_zk_session') as mock_sess:
            mock_sess.return_value.__enter__.return_value = conn
            self.env['zkteco.device']._cron_pull_tcp_devices()
