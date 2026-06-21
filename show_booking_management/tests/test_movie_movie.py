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
from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestMovieMovie(TransactionCase):
    """Test cases for movie.movie model functions."""

    def setUp(self):
        super(TestMovieMovie, self).setUp()
        self.lang = self.env['res.lang'].search([('active', '=', True)], limit=1)
        self.screen = self.env['movie.screen'].create({
            'name': 'Screen A',
            'total_rows': 10,
            'no_of_seat_row': 10,
        })
        self.time_slot = self.env['time.slots'].create({
            'movie_time': '14:00',
        })
        self.today = fields.Date.today()
        self.movie = self.env['movie.movie'].create({
            'name': 'Test Movie',
            'release_date': self.today - timedelta(days=10),
            'show_start_date': self.today,
            'show_end_date': self.today + timedelta(days=30),
            'booking_start_date': self.today - timedelta(days=5),
            'booking_end_date': self.today + timedelta(days=5),
            'price': 150.0,
            'available_screens_ids': [(4, self.screen.id)],
            'available_time_slots_ids': [(4, self.time_slot.id)],
            'prebooking_slot': 50,
        })

    # -------------------------------------------------------------------------
    # _compute_is_prebooking_closed
    # -------------------------------------------------------------------------
    def test_compute_is_prebooking_closed_not_prebooking(self):
        """Test that is_prebooking_closed is False when state is not prebooking."""
        self.movie.action_prebooking()
        self.movie.state = 'draft'
        self.movie._compute_is_prebooking_closed()
        self.assertFalse(self.movie.is_prebooking_closed)

    def test_compute_is_prebooking_closed_no_slots(self):
        """Test is_prebooking_closed is False when prebooking_slot <= 0."""
        self.movie.action_prebooking()
        self.movie.prebooking_slot = 0
        self.movie._compute_is_prebooking_closed()
        self.assertFalse(self.movie.is_prebooking_closed)

    # -------------------------------------------------------------------------
    # _check_show_start_date
    # -------------------------------------------------------------------------
    def test_check_show_start_date_valid(self):
        """Test no error when show_start_date >= release_date."""
        try:
            self.movie._check_show_start_date()
        except ValidationError:
            self.fail("_check_show_start_date raised ValidationError unexpectedly")

    def test_check_show_start_date_before_release(self):
        """Test ValidationError when show_start_date < release_date."""
        with self.assertRaises(ValidationError):
            self.env['movie.movie'].create({
                'name': 'Invalid Movie',
                'release_date': self.today + timedelta(days=5),
                'show_start_date': self.today,
                'show_end_date': self.today + timedelta(days=10),
                'price': 100.0,
            })

    def test_check_show_end_before_start(self):
        """Test ValidationError when show_end_date < show_start_date."""
        with self.assertRaises(ValidationError):
            self.env['movie.movie'].create({
                'name': 'Bad Dates Movie',
                'release_date': self.today - timedelta(days=10),
                'show_start_date': self.today + timedelta(days=10),
                'show_end_date': self.today,
                'price': 100.0,
            })

    # -------------------------------------------------------------------------
    # _check_booking_dates
    # -------------------------------------------------------------------------
    def test_check_booking_dates_valid(self):
        """Test no error with valid booking dates."""
        try:
            self.movie._check_booking_dates()
        except ValidationError:
            self.fail("_check_booking_dates raised ValidationError unexpectedly")

    def test_check_booking_start_after_show_start(self):
        """Test ValidationError when booking_start_date > show_start_date."""
        with self.assertRaises(ValidationError):
            self.env['movie.movie'].create({
                'name': 'Booking Dates Movie',
                'release_date': self.today - timedelta(days=10),
                'show_start_date': self.today,
                'show_end_date': self.today + timedelta(days=30),
                'booking_start_date': self.today + timedelta(days=5),
                'booking_end_date': self.today + timedelta(days=10),
                'price': 100.0,
            })

    def test_check_booking_end_before_start(self):
        """Test ValidationError when booking_end_date < booking_start_date."""
        with self.assertRaises(ValidationError):
            self.env['movie.movie'].create({
                'name': 'Bad Booking Movie',
                'release_date': self.today - timedelta(days=10),
                'show_start_date': self.today + timedelta(days=10),
                'show_end_date': self.today + timedelta(days=30),
                'booking_start_date': self.today + timedelta(days=5),
                'booking_end_date': self.today + timedelta(days=1),
                'price': 100.0,
            })

    # -------------------------------------------------------------------------
    # _check_screen_availability
    # -------------------------------------------------------------------------
    def test_check_screen_availability_no_overlap(self):
        """Test no error when screens do not overlap with existing movies."""
        try:
            self.movie._check_screen_availability()
        except ValidationError:
            self.fail("_check_screen_availability raised ValidationError unexpectedly")

    def test_check_screen_availability_overlap(self):
        """Test ValidationError when screen is double-booked."""
        with self.assertRaises(ValidationError):
            self.env['movie.movie'].create({
                'name': 'Overlapping Movie',
                'release_date': self.today - timedelta(days=10),
                'show_start_date': self.today + timedelta(days=5),
                'show_end_date': self.today + timedelta(days=15),
                'price': 200.0,
                'available_screens_ids': [(4, self.screen.id)],
            })

    # -------------------------------------------------------------------------
    # check_shows_on_date
    # -------------------------------------------------------------------------
    def test_check_shows_on_date_true(self):
        """Test returns True when the movie runs on the specified date."""
        result = self.env['movie.movie'].check_shows_on_date(
            str(self.today + timedelta(days=10)), self.movie.id
        )
        self.assertTrue(result)

    def test_check_shows_on_date_false(self):
        """Test returns False when the movie does not run on the specified date."""
        result = self.env['movie.movie'].check_shows_on_date(
            str(self.today + timedelta(days=100)), self.movie.id
        )
        self.assertFalse(result)

    # -------------------------------------------------------------------------
    # action_prebooking
    # -------------------------------------------------------------------------
    def test_action_prebooking(self):
        """Test action_prebooking transitions state to 'prebooking'."""
        self.movie.action_prebooking()
        self.assertEqual(self.movie.state, 'prebooking')

    # -------------------------------------------------------------------------
    # action_start_show
    # -------------------------------------------------------------------------
    def test_action_start_show(self):
        """Test action_start_show transitions state to 'ongoing' on valid date."""
        self.movie.action_prebooking()
        # show_start_date is today so this should be valid
        self.movie.action_start_show()
        self.assertEqual(self.movie.state, 'ongoing')

    def test_action_start_show_future_date(self):
        """Test action_start_show raises ValidationError before show_start_date."""
        self.movie.action_prebooking()
        self.movie.show_start_date = self.today + timedelta(days=5)
        with self.assertRaises(ValidationError):
            self.movie.action_start_show()

    # -------------------------------------------------------------------------
    # action_cancel_show
    # -------------------------------------------------------------------------
    def test_action_cancel_show(self):
        """Test action_cancel_show transitions state to 'cancel'."""
        self.movie.action_cancel_show()
        self.assertEqual(self.movie.state, 'cancel')

    # -------------------------------------------------------------------------
    # _cron_auto_start_shows
    # -------------------------------------------------------------------------
    def test_cron_auto_start_shows(self):
        """Test cron auto-starts prebooking movies whose show_start_date has passed."""
        self.movie.action_prebooking()
        self.env['movie.movie']._cron_auto_start_shows()
        # show_start_date is today, so should now be ongoing
        self.assertEqual(self.movie.state, 'ongoing')

    def test_cron_auto_cancel_expired_shows(self):
        """Test cron cancels movies past their show_end_date."""
        self.movie.action_prebooking()
        # Write both dates together so end >= start constraint is satisfied
        self.movie.write({
            'show_start_date': self.today - timedelta(days=5),
            'show_end_date': self.today - timedelta(days=1),
        })
        self.env['movie.movie']._cron_auto_start_shows()
        self.assertEqual(self.movie.state, 'cancel')

    # -------------------------------------------------------------------------
    # update_seats
    # -------------------------------------------------------------------------
    def test_update_seats(self):
        """Test update_seats returns correct seat availability info."""
        result = self.env['movie.movie'].update_seats(
            self.screen.id, self.time_slot.id, str(self.today)
        )
        self.assertIn('booked_seats', result)
        self.assertIn('booked_seats_count', result)
        self.assertIn('available_seats_count', result)
        self.assertEqual(result['booked_seats_count'], 0)
        self.assertEqual(result['available_seats_count'], self.screen.total_seat_count)
