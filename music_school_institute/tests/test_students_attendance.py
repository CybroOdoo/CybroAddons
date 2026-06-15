# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from datetime import date

@tagged('-at_install', 'post_install')
class TestStudentsAttendance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestStudentsAttendance, cls).setUpClass()
        
        # Create a student
        cls.student = cls.env['res.partner'].create({
            'name': 'Test Student',
            'student': True,
        })

    def test_01_create_attendance(self):
        """Test creating an attendance record."""
        attendance = self.env['students.attendance'].create({
            'student_id': self.student.id,
            'attendance': 'present',
            'date': date.today(),
        })
        
        self.assertEqual(attendance.student_id, self.student)
        self.assertEqual(attendance.attendance, 'present')
        self.assertEqual(attendance.date, date.today())
