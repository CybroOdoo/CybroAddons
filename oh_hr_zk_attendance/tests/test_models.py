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
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestZkAttendanceBase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.partner_admin")
        cls.employee = cls.env.ref("hr.employee_admin", raise_if_not_found=False) or cls.env["hr.employee"].search([], limit=1)
        cls.device = cls.env["biometric.device.details"].create({
            "name": "Test Device",
            "device_ip": "192.168.1.10",
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


class TestHrEmployee(TestZkAttendanceBase):
    def test_action_biometric_device_returns_wizard_action(self):
        action = self.employee.action_biometric_device()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["target"], "new")
        self.assertEqual(action["res_model"], "employee.biometric")
        self.assertEqual(action["context"]["default_employee_id"], self.employee.id)


class TestResConfigSettings(TestZkAttendanceBase):
    def _cron(self):
        return self.env.ref(
            "oh_hr_zk_attendance.ir_cron_schedule_attendance_action",
            raise_if_not_found=False,
        ) or self.env["ir.cron"].search(
            [("name", "=", "Schedule Attendance Downloading")],
            limit=1,
        )

    def test_set_values_enables_cron_with_hour_interval(self):
        cron = self._cron()
        self.assertTrue(cron)

        settings = self.env["res.config.settings"].create({
            "schedule_attendance_downloads": True,
            "schedule_time_interval": 3,
            "schedule_time_period": "hours",
        })

        with patch("odoo.addons.oh_hr_zk_attendance.models.res_config_settings.fields.Datetime.now",
                   return_value=datetime(2026, 5, 14, 12, 0, 0)):
            settings.set_values()

        cron.invalidate_recordset()
        self.assertTrue(cron.active)
        self.assertEqual(cron.interval_type, "hours")
        self.assertEqual(cron.interval_number, 3)

    def test_set_values_disables_cron(self):
        cron = self._cron()
        self.assertTrue(cron)

        settings = self.env["res.config.settings"].create({
            "schedule_attendance_downloads": False,
        })
        settings.set_values()

        cron.invalidate_recordset()
        self.assertFalse(cron.active)


class TestDailyAttendance(TestZkAttendanceBase):
    def test_init_recreates_sql_view(self):
        model = self.env["daily.attendance"]

        with patch("odoo.addons.oh_hr_zk_attendance.models.daily_attendance.tools.drop_view_if_exists") as drop_view, patch.object(
            model.env.cr, "execute"
        ) as execute:
            model.init()

        drop_view.assert_called_once_with(model.env.cr, "daily_attendance")
        execute.assert_called_once()
        self.assertIn("create or replace view daily_attendance", execute.call_args.args[0].lower())


class TestZkMachineAttendance(TestZkAttendanceBase):
    def test_overtime_methods_are_neutralized(self):
        attendance = self.env["zk.machine.attendance"].create({
            "employee_id": self.employee.id,
            "check_in": "2026-05-14 09:00:00",
            "check_out": "2026-05-14 17:00:00",
            "device_id_num": "EMP001",
            "punch_type": "0",
            "attendance_type": "1",
            "punching_time": "2026-05-14 09:00:00",
            "address_id": self.partner.id,
            "company_id": self.env.company.id,
        })

        attendance._check_validity()
        self.assertEqual(attendance._get_overtimes_to_update_domain(), [])
        self.assertIsNone(attendance._update_overtime())

    def test_computed_overtime_fields_are_zero(self):
        attendance = self.env["zk.machine.attendance"].create({
            "employee_id": self.employee.id,
            "check_in": "2026-05-14 09:00:00",
            "check_out": "2026-05-14 17:00:00",
            "device_id_num": "EMP002",
            "punch_type": "1",
            "attendance_type": "15",
            "punching_time": "2026-05-14 17:00:00",
            "address_id": self.partner.id,
            "company_id": self.env.company.id,
        })

        attendance._compute_overtime_hours()
        attendance._compute_validated_overtime_hours()

        self.assertEqual(attendance.overtime_hours, 0.0)
        self.assertEqual(attendance.validated_overtime_hours, 0.0)
