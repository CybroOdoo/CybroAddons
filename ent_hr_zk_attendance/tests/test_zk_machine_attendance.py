# -*- coding: utf-8 -*-

from odoo.addons.ent_hr_zk_attendance.tests.common import EntZkTransactionCase


class TestZkMachineAttendance(EntZkTransactionCase):
    def test_overtime_methods_are_neutralized(self):
        attendance = self.env["zk.machine.attendance"].create({
            "employee_id": self.employee.id,
            "check_in": "2026-05-14 09:00:00",
            "check_out": "2026-05-14 17:00:00",
            "device_id_no": "EMP001",
            "punch_type": "0",
            "attendance_type": "1",
            "punching_time": "2026-05-14 09:00:00",
            "address_id": self.partner.id,
        })

        attendance._check_validity()
        self.assertEqual(attendance._get_overtimes_to_update_domain(), [])
        self.assertIsNone(attendance._update_overtime())

    def test_computed_overtime_fields_are_zero(self):
        attendance = self.env["zk.machine.attendance"].create({
            "employee_id": self.employee.id,
            "check_in": "2026-05-14 09:00:00",
            "check_out": "2026-05-14 17:00:00",
            "device_id_no": "EMP002",
            "punch_type": "1",
            "attendance_type": "15",
            "punching_time": "2026-05-14 17:00:00",
            "address_id": self.partner.id,
        })

        attendance._compute_overtime_hours()
        attendance._compute_validated_overtime_hours()

        self.assertEqual(attendance.overtime_hours, 0.0)
        self.assertEqual(attendance.validated_overtime_hours, 0.0)
