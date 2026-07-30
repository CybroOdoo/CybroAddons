# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from datetime import date, timedelta
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError



class TestMovieMovie(TransactionCase):
    """Test cases for movie.movie model"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Movie = cls.env['movie.movie']

        cls.screen_1 = cls.env['movie.screen'].create({
            'name': 'Screen A',
            'total_rows': 10,
            'no_of_seat_row': 10,  # 100 seats
        })
        cls.screen_2 = cls.env['movie.screen'].create({
            'name': 'Screen B',
            'total_rows': 5,
            'no_of_seat_row': 10,  # 50 seats
        })
        cls.time_slot_1 = cls.env['time.slots'].search([('movie_time', '=', '10.00')], limit=1) or cls.env['time.slots'].create({'movie_time': '10:00'})
        cls.time_slot_2 = cls.env['time.slots'].search([('movie_time', '=', '15.00')], limit=1) or cls.env['time.slots'].create({'movie_time': '15:00'})
        cls.show_type = cls.env['show.type'].create({'name': '3D'})

        cls.today = date.today()
        cls.yesterday = cls.today - timedelta(days=1)
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.next_week = cls.today + timedelta(days=7)

        cls.movie = cls.Movie.create({
            'name': 'Inception',
            'duration': 2.5,
            'release_date': cls.today,
            'show_start_date': cls.today,
            'show_end_date': cls.next_week,
            'booking_start_date': cls.today,
            'booking_end_date': cls.next_week,
            'prebooking_slot': 50,
            'price': 150.0,
            'about_movie': 'A mind-bending thriller.',
            'show_type_ids': [(4, cls.show_type.id)],
            'available_screens_ids': [(4, cls.screen_1.id)],
            'available_time_slots_ids': [(4, cls.time_slot_1.id)],
        })

    # ── Creation ──────────────────────────────────────────────────────────────

    def test_movie_creation_defaults(self):
        """New movie defaults to draft state"""
        self.assertEqual(self.movie.state, 'draft')
        self.assertEqual(self.movie.name, 'Inception')
        self.assertEqual(self.movie.price, 150.0)

    def test_movie_currency_default(self):
        """Currency defaults to company currency"""
        self.assertTrue(self.movie.currency_id)
        self.assertEqual(self.movie.currency_id, self.env.user.company_id.currency_id)

    # ── Date Constraints ──────────────────────────────────────────────────────

    def test_show_start_before_release_date_raises(self):
        """show_start_date before release_date must raise ValidationError"""
        with self.assertRaises(ValidationError):
            self.Movie.create({
                'name': 'Bad Start Date',
                'release_date': self.tomorrow,
                'show_start_date': self.today,
                'show_end_date': self.next_week,
                'price': 100.0,
            })

    def test_show_end_before_show_start_raises(self):
        """show_end_date before show_start_date must raise ValidationError"""
        with self.assertRaises(ValidationError):
            self.Movie.create({
                'name': 'Bad End Date',
                'release_date': self.today,
                'show_start_date': self.next_week,
                'show_end_date': self.today,
                'price': 100.0,
            })

    def test_booking_start_after_show_start_raises(self):
        """booking_start_date after show_start_date must raise ValidationError"""
        with self.assertRaises(ValidationError):
            self.Movie.create({
                'name': 'Bad Booking Start',
                'show_start_date': self.today,
                'show_end_date': self.next_week,
                'booking_start_date': self.tomorrow,
                'booking_end_date': self.next_week,
                'price': 100.0,
            })

    def test_booking_end_before_booking_start_raises(self):
        """booking_end_date before booking_start_date must raise ValidationError"""
        with self.assertRaises(ValidationError):
            self.Movie.create({
                'name': 'Bad Booking End',
                'show_start_date': self.next_week,
                'show_end_date': self.next_week + timedelta(days=7),
                'booking_start_date': self.tomorrow,
                'booking_end_date': self.today,
                'price': 100.0,
            })

    def test_valid_dates_no_error(self):
        """Valid date combinations must not raise any error"""
        movie = self.Movie.create({
            'name': 'Valid Dates Movie',
            'release_date': self.today,
            'show_start_date': self.today,
            'show_end_date': self.next_week,
            'booking_start_date': self.today,
            'booking_end_date': self.next_week,
            'price': 100.0,
            'available_screens_ids': [(4, self.screen_2.id)],
        })
        self.assertTrue(movie.id)

    # ── Screen Availability Constraints ──────────────────────────────────────

    def test_overlapping_screen_raises(self):
        """Two movies cannot share the same screen during overlapping dates"""
        with self.assertRaises(ValidationError):
            self.Movie.create({
                'name': 'Screen Clash Movie',
                'release_date': self.today,
                'show_start_date': self.today,
                'show_end_date': self.next_week,
                'available_screens_ids': [(4, self.screen_1.id)],
                'price': 100.0,
            })

    def test_non_overlapping_dates_same_screen_allowed(self):
        """Same screen with non-overlapping dates is allowed"""
        movie = self.Movie.create({
            'name': 'After Inception',
            'release_date': self.next_week + timedelta(days=1),
            'show_start_date': self.next_week + timedelta(days=1),
            'show_end_date': self.next_week + timedelta(days=14),
            'available_screens_ids': [(4, self.screen_1.id)],
            'price': 100.0,
        })
        self.assertTrue(movie.id)

    def test_different_screen_during_overlap_allowed(self):
        """Different screen during overlapping period is allowed"""
        movie = self.Movie.create({
            'name': 'Parallel Movie',
            'release_date': self.today,
            'show_start_date': self.today,
            'show_end_date': self.next_week,
            'available_screens_ids': [(4, self.screen_2.id)],
            'price': 100.0,
        })
        self.assertTrue(movie.id)

    def test_write_triggers_screen_check(self):
        """Writing overlapping screen via write() also raises ValidationError"""
        other = self.Movie.create({
            'name': 'Write Test Movie',
            'release_date': self.today,
            'show_start_date': self.today,
            'show_end_date': self.next_week,
            'available_screens_ids': [(4, self.screen_2.id)],
            'price': 100.0,
        })
        with self.assertRaises(ValidationError):
            other.write({'available_screens_ids': [(4, self.screen_1.id)]})

    # ── State Transitions ─────────────────────────────────────────────────────

    def test_action_prebooking(self):
        """action_prebooking changes state to prebooking"""
        movie = self.Movie.create({
            'name': 'Prebooking Test',
            'release_date': self.today,
            'show_start_date': self.today,
            'show_end_date': self.next_week,
            'available_screens_ids': [(4, self.screen_2.id)],
            'price': 100.0,
        })
        self.assertEqual(movie.state, 'draft')
        movie.action_prebooking()
        self.assertEqual(movie.state, 'prebooking')

    def test_action_start_show(self):
        """action_start_show changes state to ongoing when booking date is today"""
        movie = self.Movie.create({
            'name': 'Start Show Test',
            'release_date': self.today,
            'show_start_date': self.today,
            'show_end_date': self.next_week,
            'booking_start_date': self.today,
            'available_screens_ids': [(4, self.screen_2.id)],
            'price': 100.0,
        })
        movie.action_prebooking()
        movie.action_start_show()
        self.assertEqual(movie.state, 'ongoing')

    def test_action_start_show_too_early_raises(self):
        """action_start_show before booking_start_date raises ValidationError"""
        movie = self.Movie.create({
            'name': 'Too Early Start',
            'release_date': self.today,
            'show_start_date': self.next_week,
            'show_end_date': self.next_week + timedelta(days=7),
            'booking_start_date': self.next_week,
            'available_screens_ids': [(4, self.screen_2.id)],
            'price': 100.0,
        })
        movie.action_prebooking()
        with self.assertRaises(ValidationError):
            movie.action_start_show()

    def test_action_cancel_show(self):
        """action_cancel_show changes state to cancel from any state"""
        self.movie.action_cancel_show()
        self.assertEqual(self.movie.state, 'cancel')
        # Reset for other tests
        self.movie.write({'state': 'draft'})

    def test_full_state_lifecycle(self):
        """draft → prebooking → ongoing → cancel"""
        movie = self.Movie.create({
            'name': 'Lifecycle Movie',
            'release_date': self.today,
            'show_start_date': self.today,
            'show_end_date': self.next_week,
            'booking_start_date': self.today,
            'available_screens_ids': [(4, self.screen_2.id)],
            'price': 100.0,
        })
        self.assertEqual(movie.state, 'draft')
        movie.action_prebooking()
        self.assertEqual(movie.state, 'prebooking')
        movie.action_start_show()
        self.assertEqual(movie.state, 'ongoing')
        movie.action_cancel_show()
        self.assertEqual(movie.state, 'cancel')

    # ── check_shows_on_date ───────────────────────────────────────────────────

    def test_check_shows_on_date_within_range(self):
        """Returns True when date is within show dates"""
        result = self.Movie.check_shows_on_date(self.today, self.movie.id)
        self.assertTrue(result)

    def test_check_shows_on_date_out_of_range(self):
        """Returns False when date is outside show dates"""
        past = self.today - timedelta(days=30)
        result = self.Movie.check_shows_on_date(past, self.movie.id)
        self.assertFalse(result)

    def test_check_shows_on_end_date(self):
        """Returns True on the last day of show"""
        result = self.Movie.check_shows_on_date(self.next_week, self.movie.id)
        self.assertTrue(result)

    # ── is_prebooking_closed compute ─────────────────────────────────────────

    def test_prebooking_not_closed_when_draft(self):
        """is_prebooking_closed is False when state is not prebooking"""
        self.assertFalse(self.movie.is_prebooking_closed)

    def test_prebooking_not_closed_when_slot_zero(self):
        """is_prebooking_closed is False when prebooking_slot is 0"""
        movie = self.Movie.create({
            'name': 'Zero Slot Movie',
            'release_date': self.today,
            'show_start_date': self.today,
            'show_end_date': self.next_week,
            'prebooking_slot': 0,
            'available_screens_ids': [(4, self.screen_2.id)],
            'price': 100.0,
        })
        movie.action_prebooking()
        self.assertFalse(movie.is_prebooking_closed)

    def test_prebooking_open_when_slots_available(self):
        """is_prebooking_closed is False when there are available slots"""
        movie = self.Movie.create({
            'name': 'Open Slot Movie',
            'release_date': self.today,
            'show_start_date': self.today,
            'show_end_date': self.next_week,
            'prebooking_slot': 20,
            'available_screens_ids': [(4, self.screen_2.id)],
            'available_time_slots_ids': [(4, self.time_slot_2.id)],
            'price': 100.0,
        })
        movie.action_prebooking()
        self.assertFalse(movie.is_prebooking_closed)

    # ── update_seats ──────────────────────────────────────────────────────────

    def test_update_seats_initially_empty(self):
        """update_seats returns 0 booked seats when no seat records exist"""
        result = self.Movie.update_seats(
            self.screen_1.id, self.time_slot_1.id, self.today)
        self.assertEqual(result['booked_seats_count'], 0)
        self.assertEqual(result['available_seats_count'], 100)
        self.assertEqual(result['time_slot'], self.time_slot_1.name)
        self.assertIsInstance(result['booked_seats'], list)

    def test_update_seats_reflects_booked(self):
        """update_seats correctly reflects booked seat records"""
        # Create a dummy registration to satisfy the FK
        partner = self.env['res.partner'].create({'name': 'Seat Test Partner'})
        reg = self.env['movie.registration'].create({
            'partner_id': partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.time_slot_1.id,
            'screen_id': self.screen_1.id,
            'no_of_tickets': 2,
        })
        self.env['movie.seats'].create([
            {'screen_id': self.screen_1.id, 'time_slot_id': self.time_slot_1.id,
             'movie_registration_id': reg.id, 'date': self.today,
             'seat': 'A1', 'is_booked': True},
            {'screen_id': self.screen_1.id, 'time_slot_id': self.time_slot_1.id,
             'movie_registration_id': reg.id, 'date': self.today,
             'seat': 'A2', 'is_booked': True},
        ])
        result = self.Movie.update_seats(
            self.screen_1.id, self.time_slot_1.id, self.today)
        self.assertEqual(result['booked_seats_count'], 2)
        self.assertIn('A1', result['booked_seats'])
        self.assertIn('A2', result['booked_seats'])

    # ── cron ──────────────────────────────────────────────────────────────────

    def test_cron_auto_start_shows(self):
        """Cron transitions prebooking movies with past show_start_date to ongoing"""
        movie = self.Movie.create({
            'name': 'Cron Test Movie',
            'release_date': self.today,
            'show_start_date': self.today,
            'show_end_date': self.next_week,
            'booking_start_date': self.today,
            'available_screens_ids': [(4, self.screen_2.id)],
            'price': 100.0,
        })
        movie.write({'state': 'prebooking'})
        self.Movie._cron_auto_start_shows()
        self.assertEqual(movie.state, 'ongoing')
