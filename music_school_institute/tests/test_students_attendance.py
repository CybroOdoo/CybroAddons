# -*- coding: utf-8 -*-

from odoo import fields
from odoo.tests.common import TransactionCase


class TestStudentsAttendance(TransactionCase):

    def test_students_attendance_defaults_company_and_date(self):
        student = self.env['res.partner'].create({
            'name': 'Music Student',
            'student': True,
        })

        attendance = self.env['students.attendance'].create({
            'student_id': student.id,
            'attendance': 'present',
        })

        self.assertEqual(attendance.student_id, student)
        self.assertEqual(attendance.date, fields.Date.today())
        self.assertEqual(attendance.company_id, self.env.company)

    def test_students_attendance_allows_absent_record(self):
        student = self.env['res.partner'].create({
            'name': 'Absent Music Student',
            'student': True,
        })

        attendance = self.env['students.attendance'].create({
            'student_id': student.id,
            'attendance': 'absent',
            'date': '2026-05-04',
        })

        self.assertEqual(attendance.attendance, 'absent')
        self.assertEqual(attendance.date.strftime('%Y-%m-%d'), '2026-05-04')
