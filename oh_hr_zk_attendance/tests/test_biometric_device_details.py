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
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.oh_hr_zk_attendance.models import biometric_device_details as biometric_module


class FakeZkUser:
    def __init__(self, uid, user_id, name):
        self.uid = uid
        self.user_id = user_id
        self.name = name


class FakeFinger:
    def __init__(self, uid, fid):
        self.uid = uid
        self.fid = fid


class FakeTemplate:
    def __init__(self, template):
        self.template = template


class FakeAttendance:
    def __init__(self, user_id, timestamp, status=1, punch=0):
        self.user_id = user_id
        self.timestamp = timestamp
        self.status = status
        self.punch = punch


class TestBiometricDeviceDetails(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.partner_admin")
        cls.employee = cls.env.ref("hr.employee_admin", raise_if_not_found=False) or cls.env["hr.employee"].search([], limit=1)
        cls.device = cls.env["biometric.device.details"].create({
            "name": "Device Under Test",
            "device_ip": "192.168.1.30",
            "port_number": 4370,
            "address_id": cls.partner.id,
        })

    def setUp(self):
        super().setUp()
        self._sharepoint_upload_patcher = patch(
            "odoo.addons.odoo_sharepoint_connector.models.ir_attachment.IrAttachment._upload_to_sharepoint_if_needed",
            autospec=True,
        )
        self._sharepoint_upload_patcher.start()
        self.addCleanup(self._sharepoint_upload_patcher.stop)

    def test_device_connect_returns_connection_or_false(self):
        zk = Mock()
        zk.connect.return_value = "connection"
        self.assertEqual(self.device.device_connect(zk), "connection")

        zk.connect.side_effect = RuntimeError("boom")
        self.assertFalse(self.device.device_connect(zk))

    def test_action_test_connection_success(self):
        zk_instance = Mock()
        zk_instance.connect.return_value = True

        with patch.object(biometric_module, "ZK", return_value=zk_instance, create=True):
            action = self.device.action_test_connection()

        zk_instance.test_voice.assert_called_once_with(index=0)
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["type"], "success")

    def test_action_test_connection_wraps_errors(self):
        zk_instance = Mock()
        zk_instance.connect.side_effect = RuntimeError("no route")

        with patch.object(biometric_module, "ZK", return_value=zk_instance, create=True), self.assertRaisesRegex(
            ValidationError, "no route"
        ):
            self.device.action_test_connection()

    def test_action_clear_attendance_clears_device_and_table(self):
        conn = Mock()
        zk_instance = Mock()
        zk_instance.get_attendance.return_value = [object()]

        with patch.object(biometric_module, "ZK", return_value=zk_instance, create=True), patch.object(
            type(self.device), "device_connect", autospec=True, return_value=conn
        ), patch.object(self.device.env.cr, "execute") as execute, patch.object(
            type(self.device), "message_post", autospec=True
        ) as message_post:
            self.device.action_clear_attendance()

        conn.enable_device.assert_called_once()
        conn.clear_attendance.assert_called_once()
        execute.assert_called_once()
        message_post.assert_called_once()

    def test_action_download_attendance_raises_when_connection_fails(self):
        zk_instance = Mock()

        with patch.object(biometric_module, "ZK", return_value=zk_instance, create=True), patch.object(
            type(self.device), "device_connect", autospec=True, return_value=False
        ), self.assertRaisesRegex(UserError, "Please Check the Connection"):
            self.device.action_download_attendance()

    def test_action_download_attendance_creates_device_attendance(self):
        self.employee.write({
            "device_id": self.device.id,
            "device_id_num": "BIO-DOWNLOAD",
        })
        conn = Mock()
        user = FakeZkUser(uid=1, user_id="BIO-DOWNLOAD", name=self.employee.name)
        finger = FakeFinger(uid=1, fid=2)
        conn.get_users.return_value = [user]
        conn.get_templates.return_value = [finger]
        conn.get_user_template.return_value = FakeTemplate(b"\x01\x02")
        conn.get_attendance.return_value = [
            FakeAttendance(
                user_id="BIO-DOWNLOAD",
                timestamp=datetime(2026, 5, 14, 9, 0, 0),
                status=1,
                punch=0,
            )
        ]

        with patch.object(biometric_module, "ZK", return_value=Mock(), create=True), patch.object(
            type(self.device), "device_connect", autospec=True, return_value=conn
        ), patch.object(type(self.device), "get_device_information", autospec=True), patch.object(
            type(self.device), "get_all_users", autospec=True
        ), patch.object(type(self.device), "action_set_timezone", autospec=True):
            result = self.device.action_download_attendance()

        self.assertTrue(result)
        self.assertTrue(
            self.env["zk.machine.attendance"].search_count(
                [("device_id_num", "=", "BIO-DOWNLOAD")]
            )
        )

    def test_action_restart_device_returns_notification(self):
        conn = Mock()
        zk_instance = Mock()
        self.device.is_live_capture = True

        with patch.object(biometric_module, "ZK", return_value=zk_instance, create=True), patch.object(
            type(self.device), "device_connect", autospec=True, return_value=conn
        ), patch.object(type(self.device), "action_stop_live_capture", autospec=True) as stop_live:
            action = self.device.action_restart_device()

        stop_live.assert_called_once_with(self.device)
        conn.restart.assert_called_once()
        self.assertEqual(action["params"]["type"], "success")

    def test_schedule_attendance_respects_live_capture_state(self):
        with patch.object(type(self.device), "action_download_attendance", autospec=True) as download, patch.object(
            type(self.device), "action_stop_live_capture", autospec=True
        ) as stop_live, patch.object(
            type(self.device), "action_live_capture", autospec=True
        ) as live_capture:
            self.device.is_live_capture = True
            self.device.schedule_attendance()

        stop_live.assert_called_once_with(self.device)
        download.assert_called_once_with(self.device)
        live_capture.assert_called_once_with(self.device)

    def test_action_live_capture_starts_thread(self):
        fake_thread = Mock()

        with patch.object(type(self.device), "action_set_timezone", autospec=True), patch.object(
            biometric_module, "ZKBioAttendance", return_value=fake_thread
        ):
            action = self.device.action_live_capture()

        self.assertTrue(self.device.is_live_capture)
        fake_thread.start.assert_called_once()
        self.assertEqual(action["tag"], "reload")

    def test_action_stop_live_capture_stops_global_thread(self):
        old_thread = biometric_module.live_capture_thread
        biometric_module.live_capture_thread = Mock()
        self.device.is_live_capture = True
        try:
            action = self.device.action_stop_live_capture()
        finally:
            biometric_module.live_capture_thread = old_thread

        self.assertFalse(self.device.is_live_capture)
        self.assertEqual(action["tag"], "reload")

    def test_action_set_timezone_sets_device_time(self):
        conn = Mock()
        zk_instance = Mock()

        with patch.object(biometric_module, "ZK", return_value=zk_instance, create=True), patch.object(
            type(self.device), "device_connect", autospec=True, return_value=conn
        ), patch.object(
            biometric_module.fields.Datetime, "now", return_value=datetime(2026, 5, 14, 12, 0, 0)
        ):
            action = self.device.action_set_timezone()

        conn.set_time.assert_called_once()
        self.assertEqual(action["params"]["type"], "success")

    def test_get_all_users_updates_existing_employee(self):
        self.employee.write({"device_id": self.device.id, "device_id_num": "BIO-USER"})
        conn = Mock()
        conn.get_users.return_value = [FakeZkUser(1, "BIO-USER", "Updated Name")]
        zk_instance = Mock()

        with patch.object(biometric_module, "ZK", return_value=zk_instance, create=True), patch.object(
            type(self.device), "device_connect", autospec=True, return_value=conn
        ):
            self.device.get_all_users()

        self.assertEqual(self.employee.name, "Updated Name")

    def test_set_user_assigns_device_identifier(self):
        self.employee.write({"device_id": False, "device_id_num": False})
        conn = Mock()
        conn.get_users.side_effect = [
            [FakeZkUser(1, "1", "User One")],
            [FakeZkUser(1, "1", "User One")],
            [FakeZkUser(2, "2", self.employee.name)],
            [FakeZkUser(2, "2", self.employee.name)],
        ]
        zk_instance = Mock()

        with patch.object(biometric_module, "ZK", return_value=zk_instance, create=True), patch.object(
            type(self.device), "device_connect", autospec=True, return_value=conn
        ):
            self.device.set_user(self.employee.id)

        self.assertEqual(self.employee.device_id, self.device)
        self.assertEqual(self.employee.device_id_num, "2")
        conn.set_user.assert_called_once()

    def test_delete_user_clears_employee_device_data(self):
        self.employee.write({"device_id": self.device.id, "device_id_num": "DEL-1"})
        self.env["fingerprint.templates"].create({
            "employee_id": self.employee.id,
            "finger_id": "1",
            "filename": "test.fp",
        })
        conn = Mock()
        zk_instance = Mock()

        with patch.object(biometric_module, "ZK", return_value=zk_instance, create=True), patch.object(
            type(self.device), "device_connect", autospec=True, return_value=conn
        ):
            self.device.delete_user(self.employee.id, "device_only")

        conn.delete_user.assert_called_once_with(uid=None, user_id="DEL-1")
        self.assertFalse(self.employee.device_id)
        self.assertFalse(self.employee.device_id_num)
        self.assertFalse(self.employee.fingerprint_ids)

    def test_update_user_returns_success_action(self):
        self.employee.write({"device_id": self.device.id, "device_id_num": "UPD-1"})
        conn = Mock()
        conn.get_users.return_value = [FakeZkUser(4, "UPD-1", "Old Name")]
        zk_instance = Mock()

        with patch.object(biometric_module, "ZK", return_value=zk_instance, create=True), patch.object(
            type(self.device), "device_connect", autospec=True, return_value=conn
        ):
            action = self.device.update_user(self.employee.id)

        conn.set_user.assert_called_once()
        self.assertEqual(action["params"]["type"], "success")

    def test_get_device_information_updates_fields(self):
        conn = Mock()
        conn.get_device_name.return_value = "ZKFace"
        conn.get_firmware_version.return_value = "1.0"
        conn.get_serialnumber.return_value = "SN123"
        conn.get_platform.return_value = "uFace"
        conn.get_mac.return_value = "AA:BB:CC"
        zk_instance = Mock()

        with patch.object(biometric_module, "ZK", return_value=zk_instance, create=True), patch.object(
            type(self.device), "device_connect", autospec=True, return_value=conn
        ):
            self.device.get_device_information()

        self.assertEqual(self.device.device_name, "ZKFace")
        self.assertEqual(self.device.device_firmware, "1.0")
        self.assertEqual(self.device.device_serial_no, "SN123")
        self.assertEqual(self.device.device_platform, "uFace")
        self.assertEqual(self.device.device_mac, "AA:BB:CC")


class TestZKBioAttendance(TransactionCase):
    def test_init_requires_connection(self):
        record = SimpleNamespace(env=self.env)
        zk_instance = Mock()
        zk_instance.connect.return_value = False

        with patch.object(biometric_module, "ZK", return_value=zk_instance, create=True), self.assertRaisesRegex(
            UserError, "Please Check the Connection"
        ):
            biometric_module.ZKBioAttendance("192.168.1.1", 4370, 0, record)

    def test_stop_marks_thread_stopped(self):
        instance = object.__new__(biometric_module.ZKBioAttendance)
        instance.conn = SimpleNamespace(end_live_capture=False)
        instance.stop_event = Mock()

        instance.stop()

        self.assertTrue(instance.conn.end_live_capture)
        instance.stop_event.set.assert_called_once()

    def test_run_polls_live_capture_until_stopped(self):
        instance = object.__new__(biometric_module.ZKBioAttendance)
        instance.conn = Mock()
        instance.conn.end_live_capture = False
        instance.conn.live_capture.return_value = [object()]
        instance.stop_event = Mock()
        instance.stop_event.is_set.side_effect = [False, True]
        instance._data_live_capture = Mock()
        instance.env = self.env

        with patch.object(biometric_module.time, "sleep"):
            instance.run()

        instance.conn.live_capture.assert_called_once_with(2000)
        instance._data_live_capture.assert_called_once()

    def test_data_live_capture_downloads_and_commits(self):
        new_cr = Mock()
        cursor_manager = Mock()
        cursor_manager.__enter__ = Mock(return_value=new_cr)
        cursor_manager.__exit__ = Mock(return_value=False)
        fake_registry = Mock()
        fake_registry.cursor.return_value = cursor_manager
        record = Mock()
        record.env = self.env
        record.with_env.return_value = record
        conn = Mock()
        conn.get_attendance.return_value = [object()]

        instance = object.__new__(biometric_module.ZKBioAttendance)
        instance.conn = conn
        instance.record = record
        instance.env = self.env

        with patch.object(biometric_module, "registry", return_value=fake_registry):
            with patch.object(biometric_module.api, "Environment", return_value=Mock()):
                instance._data_live_capture()

        record.with_env.assert_called_once()
        record.action_download_attendance.assert_called_once()
        new_cr.commit.assert_called_once()
