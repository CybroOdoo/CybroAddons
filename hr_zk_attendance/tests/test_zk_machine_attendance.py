# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestZkMachineAttendance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'ZK Attendance Employee',
        })

    def test_overlapping_machine_attendance_is_allowed(self):
        first_attendance = self.env['zk.machine.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-04 09:00:00',
            'check_out': '2026-05-04 12:00:00',
            'punching_time': '2026-05-04 09:00:00',
            'device_id_num': '1001',
        })
        second_attendance = self.env['zk.machine.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-04 11:00:00',
            'check_out': '2026-05-04 13:00:00',
            'punching_time': '2026-05-04 11:00:00',
            'device_id_num': '1001',
        })

        self.assertTrue(first_attendance)
        self.assertTrue(second_attendance)

    def test_machine_attendance_stores_biometric_fields(self):
        attendance = self.env['zk.machine.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-04 09:00:00',
            'punching_time': '2026-05-04 09:00:00',
            'device_id_num': '1001',
            'attendance_type': '15',
            'punch_type': '0',
        })

        self.assertEqual(attendance.device_id_num, '1001')
        self.assertEqual(attendance.attendance_type, '15')
        self.assertEqual(attendance.punch_type, '0')
