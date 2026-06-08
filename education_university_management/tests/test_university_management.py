# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests.common import TransactionCase
from datetime import date

class TestUniversityManagement(TransactionCase):

    def setUp(self):
        super(TestUniversityManagement, self).setUp()
        self.course = self.env['university.course'].create({
            'name': 'BTech Computer Science',
            'category': 'ug',
            'no_semester': 8
        })

        self.department = self.env['university.department'].create({
            'name': 'Computer Science Department',
            'code': 'CS',
            'course_id': self.course.id,
        })

        self.semester = self.env['university.semester'].create({
            'semester_no': 1,
            'department_id': self.department.id,
        })

    def test_course_creation(self):
        """Test the creation of a university course."""
        self.assertEqual(self.course.name, 'BTech Computer Science')
        self.assertEqual(self.course.category, 'ug')
        self.assertEqual(self.course.no_semester, 8)

    def test_department_creation(self):
        """Test the creation of a university department."""
        self.assertEqual(self.department.name, 'Computer Science Department')
        self.assertEqual(self.department.code, 'CS')
        self.assertEqual(self.department.course_id, self.course)

    def test_student_creation(self):
        """Test the creation of a university student."""
        student = self.env['university.student'].create({
            'name': 'John Doe',
            'last_name': 'Smith',
            'date_of_birth': date(2000, 1, 1),
            'gender': 'male',
            'blood_group': 'o+',
            'semester_id': self.semester.id,
        })
        self.assertEqual(student.name, 'John Doe')
        self.assertEqual(student.last_name, 'Smith')
        self.assertEqual(student.gender, 'male')
        self.assertEqual(student.semester_id, self.semester)
        self.assertEqual(student.department_id, self.department)
        self.assertEqual(student.course_id, self.course)

    def test_application_creation(self):
        """Test the creation of a university application."""
        guardian = self.env['res.partner'].create({
            'name': 'Jane Doe',
            'is_parent': True,
        })
        application = self.env['university.application'].create({
            'name': 'Mark',
            'last_name': 'Smith',
            'course_id': self.course.id,
            'department_id': self.department.id,
            'semester_id': self.semester.id,
            'email': 'mark@test.com',
            'mobile': '1234567890',
            'date_of_birth': date(2000, 1, 1),
            'guardian_id': guardian.id,
        })
        self.assertEqual(application.name, 'Mark')
        self.assertEqual(application.state, 'draft')
        self.assertEqual(application.course_id, self.course)

