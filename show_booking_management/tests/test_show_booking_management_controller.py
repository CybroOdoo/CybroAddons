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
from datetime import timedelta
from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.addons.show_booking_management.controller.show_booking_management import MovieShow


@tagged('post_install', '-at_install')
class TestShowBookingManagementController(TransactionCase):
    """Test cases for show_booking_management controller routes and business logic."""

    def setUp(self):
        super(TestShowBookingManagementController, self).setUp()
        self.today = fields.Date.today()
        self.screen = self.env['movie.screen'].create({
            'name': 'Screen Controller',
            'total_rows': 10,
            'no_of_seat_row': 10,
        })
        self.time_slot = self.env['time.slots'].create({
            'movie_time': '20:00',
        })
        self.movie = self.env['movie.movie'].create({
            'name': 'Controller Test Movie',
            'release_date': self.today - timedelta(days=5),
            'show_start_date': self.today,
            'show_end_date': self.today + timedelta(days=30),
            'booking_start_date': self.today - timedelta(days=2),
            'booking_end_date': self.today + timedelta(days=10),
            'price': 250.0,
            'available_screens_ids': [(4, self.screen.id)],
            'available_time_slots_ids': [(4, self.time_slot.id)],
        })

    # -------------------------------------------------------------------------
    # show_movies route — validate controller class and route registration
    # -------------------------------------------------------------------------
    def test_show_movies_route_registered(self):
        """Test that the show_movies route is registered on the MovieShow controller."""
        from odoo.http import Controller
        self.assertTrue(issubclass(MovieShow, Controller))
        self.assertTrue(hasattr(MovieShow, 'show_movies'))

    # -------------------------------------------------------------------------
    # show_movies business logic — movies search
    # -------------------------------------------------------------------------
    def test_show_movies_business_logic_ongoing(self):
        """Test business logic: ongoing movies are returned for the /show page."""
        self.movie.action_prebooking()
        self.movie.action_start_show()
        movies = self.env['movie.movie'].search([
            '|', ('state', '=', 'ongoing'),
            '&', ('state', '=', 'prebooking'),
            '&', ('booking_start_date', '<=', self.today),
            '|', ('booking_end_date', '>=', self.today),
                 ('booking_end_date', '=', False)
        ])
        self.assertIn(self.movie, movies)

    def test_show_movies_business_logic_excludes_draft(self):
        """Test business logic: draft movies are excluded from the /show page."""
        movies = self.env['movie.movie'].search([
            '|', ('state', '=', 'ongoing'),
            '&', ('state', '=', 'prebooking'),
            '&', ('booking_start_date', '<=', self.today),
            '|', ('booking_end_date', '>=', self.today),
                 ('booking_end_date', '=', False)
        ])
        self.assertNotIn(self.movie, movies)  # movie is still in draft state

    # -------------------------------------------------------------------------
    # book_now route — validate route registration
    # -------------------------------------------------------------------------
    def test_book_now_route_registered(self):
        """Test that book_now route is registered on the MovieShow controller."""
        self.assertTrue(hasattr(MovieShow, 'book_now'))

    # -------------------------------------------------------------------------
    # book_now business logic — movie browsing
    # -------------------------------------------------------------------------
    def test_book_now_business_logic(self):
        """Test business logic: movie is retrievable by ID as in book_now."""
        movie = self.env['movie.movie'].browse(self.movie.id)
        self.assertEqual(movie.name, 'Controller Test Movie')
        self.assertTrue(movie.exists())

    # -------------------------------------------------------------------------
    # book_ticket route — validate route registration
    # -------------------------------------------------------------------------
    def test_book_ticket_route_registered(self):
        """Test that book_ticket route is registered on the MovieShow controller."""
        self.assertTrue(hasattr(MovieShow, 'book_ticket'))

    # -------------------------------------------------------------------------
    # book_ticket business logic — booked seats search
    # -------------------------------------------------------------------------
    def test_book_ticket_business_logic_booked_seats(self):
        """Test business logic: booked seats for a screen/slot/date are retrieved."""
        self.env['movie.seats'].create({
            'screen_id': self.screen.id,
            'time_slot_id': self.time_slot.id,
            'movie_registration_id': self.env['movie.registration'].create({
                'movie_id': self.movie.id,
                'date': self.today,
                'time_slot_id': self.time_slot.id,
                'screen_id': self.screen.id,
            }).id,
            'date': self.today,
            'seat': 'B1',
            'is_booked': True,
        })
        booked_seats = self.env['movie.seats'].search([
            ('screen_id', '=', self.screen.id),
            ('time_slot_id', '=', self.time_slot.id),
            ('date', '=', self.today),
            ('is_booked', '=', True),
        ]).mapped('seat')
        self.assertIn('B1', booked_seats)

    # -------------------------------------------------------------------------
    # confirm_booking route — validate route registration
    # -------------------------------------------------------------------------
    def test_confirm_booking_route_registered(self):
        """Test that confirm_booking route is registered on the MovieShow controller."""
        self.assertTrue(hasattr(MovieShow, 'confirm_booking'))
