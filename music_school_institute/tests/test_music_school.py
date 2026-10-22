# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import date
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestMusicSchool(TransactionCase):
    """Test cases for Music School Institute module."""

    def setUp(self):
        """Set up test data."""
        super().setUp()

        self.student = self.env['res.partner'].create({
            'name': 'Test Student',
            'student': True,
        })

        self.teacher = self.env['hr.employee'].create({
            'name': 'Test Teacher',
            'teacher': True,
        })

        self.instrument = self.env['product.product'].create({
            'name': 'Guitar',
            'music_instrument': True,
            'lst_price': 100.0,
        })

        self.service = self.env['service.type'].create({
            'name': 'Guitar Lessons',
            'instrument': 'Guitar',
            'teacher_id': self.teacher.id,
        })

    def test_class_type_creation(self):
        """Test class type creation."""
        from_date = date(2026, 1, 1)
        to_date = date(2026, 1, 10)

        class_type = self.env['class.type'].create({
            'name': 'Guitar Class',
            'from_date': from_date,
            'to_date': to_date,
            'service_id': self.service.id,
            'instrument_id': self.instrument.id,
            'teacher_id': self.teacher.id,
            'student_ids': [(6, 0, [self.student.id])],
        })

        self.assertEqual(class_type.name, 'Guitar Class')
        self.assertEqual(class_type.state, 'draft')
        self.assertTrue(class_type.duration > 0)
        self.assertEqual(self.student.class_id, class_type)

    def test_duration_calculation(self):
        """Test duration calculation for weekdays."""
        from_date = date(2026, 1, 5)  # Monday
        to_date = date(2026, 1, 9)     # Friday

        class_type = self.env['class.type'].create({
            'name': 'Test Class',
            'from_date': from_date,
            'to_date': to_date,
            'student_ids': [(6, 0, [self.student.id])],
        })

        self.assertEqual(class_type.duration, 5)

    def test_duration_with_repeats(self):
        """Test duration calculation with specific selected workdays."""
        from_date = date(2026, 1, 5)  # Monday
        to_date = date(2026, 1, 11)    # Sunday

        class_type = self.env['class.type'].create({
            'name': 'Weekend Class',
            'from_date': from_date,
            'to_date': to_date,
            'repeats': 'weekly',
            'saturday': True,
            'sunday': True,
            'student_ids': [(6, 0, [self.student.id])],
        })

        # Exactly 2 weekend days (Saturday 10th and Sunday 11th)
        self.assertEqual(class_type.duration, 2)

    def test_class_state_workflow(self):
        """Test class state transitions."""
        from_date = date(2026, 1, 1)
        to_date = date(2026, 1, 10)

        class_type = self.env['class.type'].create({
            'name': 'Test Class',
            'from_date': from_date,
            'to_date': to_date,
            'student_ids': [(6, 0, [self.student.id])],
        })

        class_type.action_button_class_start()
        self.assertEqual(class_type.state, 'started')

        class_type.action_button_class_completed()
        self.assertEqual(class_type.state, 'completed')

        class_type.action_button_class_cancel()
        self.assertEqual(class_type.state, 'canceled')

        class_type.action_button_set_to_draft()
        self.assertEqual(class_type.state, 'draft')

    def test_invoicing_workflow(self):
        """Test creating invoice from class."""
        from_date = date(2026, 1, 5)
        to_date = date(2026, 1, 9)

        class_type = self.env['class.type'].create({
            'name': 'Invoicing Class',
            'from_date': from_date,
            'to_date': to_date,
            'instrument_id': self.instrument.id,
            'student_ids': [(6, 0, [self.student.id])],
        })
        class_type.action_button_class_start()
        class_type.action_button_class_completed()
        class_type.action_button_create_order()

        self.assertEqual(class_type.state, 'invoice')
        self.assertEqual(class_type.order_count, 1)

        # Calling again should not create duplicate invoices
        class_type.action_button_create_order()
        self.assertEqual(class_type.order_count, 1)

    def test_attendance_creation(self):
        """Test attendance record creation."""
        attendance = self.env['students.attendance'].create({
            'student_id': self.student.id,
            'attendance': 'present',
            'date': date.today(),
        })

        self.assertEqual(attendance.student_id, self.student)
        self.assertEqual(attendance.attendance, 'present')
        self.assertEqual(attendance.date, date.today())
        self.assertEqual(self.student.attendance_count, 1)

    def test_lesson_creation(self):
        """Test lesson record creation."""
        from_date = date(2026, 1, 1)
        to_date = date(2026, 1, 10)

        class_type = self.env['class.type'].create({
            'name': 'Test Class',
            'from_date': from_date,
            'to_date': to_date,
            'student_ids': [(6, 0, [self.student.id])],
        })

        lesson = self.env['class.lesson'].create({
            'name': 'Lesson 1',
            'hours': '1 hour',
            'teacher_id': self.teacher.id,
            'relation_id': class_type.id,
        })

        self.assertEqual(lesson.name, 'Lesson 1')
        self.assertEqual(lesson.relation_id, class_type)

    def test_date_validation(self):
        """Test date validation (from_date must be before to_date)."""
        from_date = date(2026, 1, 10)
        to_date = date(2026, 1, 1)

        with self.assertRaises(ValidationError):
            self.env['class.type'].create({
                'name': 'Invalid Class',
                'from_date': from_date,
                'to_date': to_date,
                'student_ids': [(6, 0, [self.student.id])],
            })
