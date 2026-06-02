# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestDailyAttendance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Daily Attendance Employee',
        })
        cls.address = cls.env['res.partner'].create({
            'name': 'Daily Attendance Office',
        })

    def test_init_creates_daily_attendance_view(self):
        self.env['daily.attendance'].init()

        self.env.cr.execute("SELECT to_regclass('daily_attendance')")
        self.assertEqual(self.env.cr.fetchone()[0], 'daily_attendance')

    def test_daily_attendance_view_exposes_machine_attendance_rows(self):
        machine_attendance = self.env['zk.machine.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-04 09:00:00',
            'check_out': '2026-05-04 18:00:00',
            'device_id_num': '1001',
            'attendance_type': '1',
            'punch_type': '0',
            'punching_time': '2026-05-04 09:00:00',
            'address_id': self.address.id,
        })

        daily_attendance = self.env['daily.attendance'].search([
            ('employee_id', '=', self.employee.id),
            ('punching_time', '=', '2026-05-04 09:00:00'),
        ])

        self.assertTrue(daily_attendance)
        self.assertEqual(daily_attendance.employee_id, self.employee)
        self.assertEqual(daily_attendance.address_id, self.address)
        self.assertEqual(
            daily_attendance.attendance_type,
            machine_attendance.attendance_type,
        )
