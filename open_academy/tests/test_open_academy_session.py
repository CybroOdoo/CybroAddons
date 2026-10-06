# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import date, timedelta
from psycopg2 import IntegrityError
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger


class TestOpenAcademySession(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestOpenAcademySession, cls).setUpClass()
        # Create a course
        cls.course = cls.env['openacademy.course'].create({
            'name': 'Python Programming 101',
            'description': 'Introduction to Python',
        })

        # Create partners
        cls.partner_instructor = cls.env['res.partner'].create({
            'name': 'John Doe (Instructor)',
            'instructor': True,
        })
        cls.partner_attendee_1 = cls.env['res.partner'].create({
            'name': 'Alice Attendee',
        })
        cls.partner_attendee_2 = cls.env['res.partner'].create({
            'name': 'Bob Attendee',
        })

    def test_session_taken_seats(self):
        """ Test calculation of taken seats percentage """
        # Case 1: Seats is zero
        session_no_seats = self.env['openacademy.session'].create({
            'name': 'No Seats Session',
            'course_id': self.course.id,
            'seats': 0,
            'attendee_ids': [(6, 0, [self.partner_attendee_1.id])],
        })
        session_no_seats._compute_taken_seats()
        self.assertEqual(session_no_seats.taken_seats, 0.0)

        # Case 2: Seats is positive
        session_with_seats = self.env['openacademy.session'].create({
            'name': 'Seats Session',
            'course_id': self.course.id,
            'seats': 10,
            'attendee_ids': [(6, 0, [self.partner_attendee_1.id, self.partner_attendee_2.id])],
        })
        session_with_seats._compute_taken_seats()
        self.assertEqual(session_with_seats.taken_seats, 20.0)

    def test_seats_warnings(self):
        """ Test the onchange method for seats and attendees """
        # Case 1: Negative seats
        session = self.env['openacademy.session'].new({
            'seats': -5,
        })
        warning = session._onchange_seats()
        self.assertTrue(warning)
        self.assertIn('negative', warning['warning']['message'])

        # Case 2: More attendees than seats
        session_overfilled = self.env['openacademy.session'].new({
            'seats': 1,
            'attendee_ids': [(6, 0, [self.partner_attendee_1.id, self.partner_attendee_2.id])],
        })
        warning_overfilled = session_overfilled._onchange_seats()
        self.assertTrue(warning_overfilled)
        self.assertIn('Increase seats', warning_overfilled['warning']['message'])

    def test_session_date_computes(self):
        """ Test start_date, duration and end_date calculations """
        start = date(2026, 6, 1) # Monday
        session = self.env['openacademy.session'].create({
            'name': 'Date test session',
            'course_id': self.course.id,
            'start_date': start,
            'duration': 5.0,
        })

        # Test compute end_date (Monday + 5 days - 1s = Friday)
        session._compute_get_end_date()
        self.assertEqual(session.end_date, date(2026, 6, 5))

        # Test inverse computation (change end_date to Saturday -> duration should become 6)
        session.end_date = date(2026, 6, 6)
        session._compute_set_end_date()
        self.assertEqual(session.duration, 6.0)

    def test_session_attendees_count(self):
        """ Test calculation of attendees count """
        session = self.env['openacademy.session'].create({
            'name': 'Attendees count test',
            'course_id': self.course.id,
            'attendee_ids': [(6, 0, [self.partner_attendee_1.id])],
        })
        session._compute_attendees_count()
        self.assertEqual(session.attendees_count, 1)

        session.attendee_ids = [(4, self.partner_attendee_2.id)]
        session._compute_attendees_count()
        self.assertEqual(session.attendees_count, 2)

    def test_instructor_not_in_attendees_constraint(self):
        """ Test ValidationError raised if instructor is in attendee list """
        with self.assertRaises(ValidationError):
            self.env['openacademy.session'].create({
                'name': 'Invalid Instructor Session',
                'course_id': self.course.id,
                'instructor_id': self.partner_instructor.id,
                'attendee_ids': [(6, 0, [self.partner_instructor.id])],
            })

    @mute_logger('odoo.sql_db')
    def test_course_sql_constraints(self):
        """ Test SQL constraints on openacademy.course """
        # Test unique name constraint
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.env['openacademy.course'].create({
                    'name': 'Python Programming 101',
                    'description': 'Another description',
                })

        # Test name not equal to description constraint
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.env['openacademy.course'].create({
                    'name': 'Python Programming 102',
                    'description': 'Python Programming 102',
                })
