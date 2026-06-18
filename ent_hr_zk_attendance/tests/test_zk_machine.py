# -*- coding: utf-8 -*-

import datetime
from struct import pack
from types import SimpleNamespace
from unittest.mock import Mock, patch

from odoo.exceptions import UserError, ValidationError

from odoo.addons.ent_hr_zk_attendance.models import zk_machine as zk_machine_module
from odoo.addons.ent_hr_zk_attendance.tests.common import EntZkTransactionCase


class TestZkMachine(EntZkTransactionCase):
    def test_device_connect_returns_connection_or_false(self):
        zk = Mock()
        zk.connect.return_value = "connected"
        self.assertEqual(self.machine.device_connect(zk), "connected")

        zk.connect.side_effect = RuntimeError("boom")
        self.assertFalse(self.machine.device_connect(zk))

    def test_action_test_connection_success(self):
        connection = Mock()
        zk_instance = Mock()

        with patch.object(zk_machine_module, "ZK", return_value=zk_instance, create=True), patch.object(
            type(self.machine), "device_connect", autospec=True, return_value=connection
        ):
            action = self.machine.action_test_connection()

        connection.disconnect.assert_called_once()
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["type"], "success")

    def test_action_test_connection_raises_for_failed_connection(self):
        with patch.object(zk_machine_module, "ZK", return_value=Mock(), create=True), patch.object(
            type(self.machine), "device_connect", autospec=True, return_value=False
        ), self.assertRaisesRegex(UserError, "Connection failed"):
            self.machine.action_test_connection()

    def test_action_clear_attendance_clears_device_data(self):
        connection = Mock()
        zk_instance = Mock()
        zk_instance.get_attendance.return_value = [object()]

        with patch.object(zk_machine_module, "ZK", return_value=zk_instance, create=True), patch.object(
            type(self.machine), "device_connect", autospec=True, return_value=connection
        ), patch.object(self.env.cr, "execute") as execute:
            self.machine.action_clear_attendance()

        connection.enable_device.assert_called_once()
        connection.clear_attendance.assert_called_once()
        connection.disconnect.assert_called_once()
        execute.assert_called_once_with("""delete from zk_machine_attendance""")

    def test_action_clear_attendance_wraps_empty_log_error(self):
        connection = Mock()
        zk_instance = Mock()
        zk_instance.get_attendance.return_value = []

        with patch.object(zk_machine_module, "ZK", return_value=zk_instance, create=True), patch.object(
            type(self.machine), "device_connect", autospec=True, return_value=connection
        ), self.assertRaisesRegex(ValidationError, "Unable to clear Attendance log"):
            self.machine.action_clear_attendance()

    def test_action_restart_device_calls_restart(self):
        connection = Mock()

        with patch.object(zk_machine_module, "ZK", return_value=Mock(), create=True), patch.object(
            type(self.machine), "device_connect", autospec=True, side_effect=[connection, connection]
        ):
            self.machine.action_restart_device()

        connection.restart.assert_called_once()

    def test_get_size_user_returns_size_for_prepare_packet(self):
        fake_zk = SimpleNamespace(data_recv=pack("HHHHI", zk_machine_module.CMD_PREPARE_DATA, 0, 0, 0, 256))
        self.assertEqual(self.machine.getSizeUser(fake_zk), 256)

    def test_zkgetuser_returns_users_or_false(self):
        zk = Mock()
        zk.get_users.return_value = ["u1"]
        self.assertEqual(self.machine.zkgetuser(zk), ["u1"])

        zk.get_users.side_effect = RuntimeError("boom")
        self.assertFalse(self.machine.zkgetuser(zk))

    def test_action_import_attendance_imports_known_employee(self):
        self.employee.write({"device_id_no": "EMP001"})
        connection = Mock()
        connection.get_users.return_value = [SimpleNamespace(user_id="EMP001", name=self.employee.name)]
        connection.get_attendance.return_value = [
            SimpleNamespace(
                user_id="EMP001",
                timestamp=datetime.datetime(2026, 5, 14, 9, 0, 0),
                status=1,
                punch=0,
            )
        ]

        with patch.object(zk_machine_module, "ZK", return_value=Mock(), create=True), patch.object(
            type(self.machine), "device_connect", autospec=True, return_value=connection
        ):
            result = self.machine.action_import_attendance()

        self.assertTrue(result)
        self.assertTrue(self.env["zk.machine.attendance"].search_count([("device_id_no", "=", "EMP001")]))

    def test_action_import_attendance_raises_when_not_connected(self):
        with patch.object(zk_machine_module, "ZK", return_value=Mock(), create=True), patch.object(
            type(self.machine), "device_connect", autospec=True, return_value=False
        ), self.assertRaisesRegex(UserError, "Unable to connect"):
            self.machine.action_import_attendance()

    def test_cron_download_calls_import_on_all_machines(self):
        with patch.object(type(self.machine), "action_import_attendance", autospec=True) as importer:
            self.env["zk.machine"].cron_download()

        self.assertGreaterEqual(importer.call_count, 1)
