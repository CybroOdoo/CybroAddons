# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestResPartner(TransactionCase):

    def test_compute_attendance_count_counts_only_present_records(self):
        student = self.env['res.partner'].create({
            'name': 'Attendance Count Student',
            'student': True,
        })
        other_student = self.env['res.partner'].create({
            'name': 'Other Attendance Student',
            'student': True,
        })
        self.env['students.attendance'].create([
            {
                'student_id': student.id,
                'attendance': 'present',
                'date': '2026-05-04',
            },
            {
                'student_id': student.id,
                'attendance': 'absent',
                'date': '2026-05-05',
            },
            {
                'student_id': other_student.id,
                'attendance': 'present',
                'date': '2026-05-04',
            },
        ])

        student._compute_attendance_count()

        self.assertEqual(student.attendance_count, 1)

    def test_action_class_attendance_view_filters_current_student(self):
        student = self.env['res.partner'].create({
            'name': 'Attendance Action Student',
            'student': True,
        })

        action = student.action_class_attendance_view()

        self.assertEqual(action['res_model'], 'students.attendance')
        self.assertEqual(action['view_mode'], 'list')
        self.assertEqual(action['domain'], [('student_id', '=', student.id)])
        self.assertEqual(action['context'], "{'create': False}")
