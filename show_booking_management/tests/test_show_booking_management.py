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
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError



class TestShowBookingManagement(TransactionCase):
    """
    Integration tests covering cross-model interactions:
    cast.type, show.type, movie.cast, movie.seats, account.move extension,
    and full booking workflow.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = date.today()
        cls.next_week = cls.today + timedelta(days=7)

        # Supporting records
        cls.cast_type = cls.env['cast.type'].create({'name': 'Lead Actor'})
        cls.show_type = cls.env['show.type'].create({'name': 'IMAX'})
        cls.cast = cls.env['movie.cast'].create({
            'name': 'John Doe',
            'cast_id': cls.cast_type.id,
        })
        cls.screen = cls.env['movie.screen'].create({
            'name': 'Integration Screen',
            'total_rows': 10,
            'no_of_seat_row': 10,  # 100 seats
        })
        cls.time_slot = cls.env['time.slots'].search([('movie_time', '=', '19.00')], limit=1) or cls.env['time.slots'].create({'movie_time': '19:00'})
        cls.partner = cls.env['res.partner'].create({'name': 'Integration Partner'})

        cls.movie = cls.env['movie.movie'].create({
            'name': 'Interstellar',
            'release_date': cls.today,
            'show_start_date': cls.today,
            'show_end_date': cls.next_week,
            'booking_start_date': cls.today,
            'prebooking_slot': 50,
            'price': 300.0,
            'state': 'ongoing',
            'show_type_ids': [(4, cls.show_type.id)],
            'movie_cast_ids': [(4, cls.cast.id)],
            'available_screens_ids': [(4, cls.screen.id)],
            'available_time_slots_ids': [(4, cls.time_slot.id)],
        })

    # ── cast.type ─────────────────────────────────────────────────────────────

    def test_cast_type_creation(self):
        """cast.type records are created with the correct name"""
        ct = self.env['cast.type'].create({'name': 'Director'})
        self.assertEqual(ct.name, 'Director')

    def test_multiple_cast_types(self):
        """Multiple distinct cast types can coexist"""
        t1 = self.env['cast.type'].create({'name': 'Producer'})
        t2 = self.env['cast.type'].create({'name': 'Supporting Actor'})
        self.assertNotEqual(t1.id, t2.id)

    # ── show.type ─────────────────────────────────────────────────────────────

    def test_show_type_required_name(self):
        """show.type requires a name (required=True)"""
        from odoo.tools import mute_logger
        with self.assertRaises(Exception), mute_logger('odoo.sql_db'):
            self.env['show.type'].create({})

    def test_show_type_linked_to_movie(self):
        """show.type is correctly linked to the movie"""
        self.assertIn(self.show_type, self.movie.show_type_ids)

    # ── movie.cast ────────────────────────────────────────────────────────────

    def test_movie_cast_creation(self):
        """movie.cast is created with name and cast_type"""
        cast = self.env['movie.cast'].create({
            'name': 'Jane Smith',
            'cast_id': self.cast_type.id,
        })
        self.assertEqual(cast.name, 'Jane Smith')
        self.assertEqual(cast.cast_id, self.cast_type)

    def test_movie_cast_linked_to_movie(self):
        """movie.cast is correctly linked through many2many"""
        self.assertIn(self.cast, self.movie.movie_cast_ids)

    # ── movie.seats ───────────────────────────────────────────────────────────

    def test_seat_creation(self):
        """movie.seats records are created with correct fields"""
        reg = self.env['movie.registration'].create({
            'partner_id': self.partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.time_slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 1,
        })
        seat = self.env['movie.seats'].create({
            'screen_id': self.screen.id,
            'time_slot_id': self.time_slot.id,
            'movie_registration_id': reg.id,
            'date': self.today,
            'seat': 'B5',
            'is_booked': True,
        })
        self.assertEqual(seat.seat, 'B5')
        self.assertTrue(seat.is_booked)
        self.assertEqual(seat.screen_id, self.screen)
        self.assertEqual(seat.movie_registration_id, reg)

    def test_seat_unbooked_default_false(self):
        """is_booked defaults to False when not specified"""
        reg = self.env['movie.registration'].create({
            'partner_id': self.partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.time_slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 1,
        })
        seat = self.env['movie.seats'].create({
            'screen_id': self.screen.id,
            'time_slot_id': self.time_slot.id,
            'movie_registration_id': reg.id,
            'date': self.today,
            'seat': 'C1',
        })
        self.assertFalse(seat.is_booked)

    # ── account.move extension ────────────────────────────────────────────────

    def test_account_move_has_movie_ticket_id_field(self):
        """account.move has the movie_ticket_id Many2one field"""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })
        self.assertFalse(move.movie_ticket_id)

    def test_account_move_movie_ticket_id_links_to_registration(self):
        """movie_ticket_id on account.move correctly links to movie.registration"""
        reg = self.env['movie.registration'].create({
            'partner_id': self.partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.time_slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 1,
        })
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'movie_ticket_id': reg.id,
        })
        self.assertEqual(move.movie_ticket_id, reg)

    # ── Full workflow integration ─────────────────────────────────────────────

    def test_full_booking_workflow(self):
        """
        Full workflow: create movie → prebooking → ongoing →
        create registration → verify seat availability → link invoice.
        """
        screen = self.env['movie.screen'].create({
            'name': 'Workflow Screen',
            'total_rows': 5,
            'no_of_seat_row': 5,  # 25 seats
        })
        slot = self.env['time.slots'].search([('movie_time', '=', '21.00')], limit=1) or self.env['time.slots'].create({'movie_time': '21:00'})
        movie = self.env['movie.movie'].create({
            'name': 'Workflow Movie',
            'release_date': self.today,
            'show_start_date': self.today,
            'show_end_date': self.next_week,
            'booking_start_date': self.today,
            'prebooking_slot': 10,
            'price': 100.0,
            'available_screens_ids': [(4, screen.id)],
            'available_time_slots_ids': [(4, slot.id)],
        })

        # Draft → Prebooking → Ongoing
        movie.action_prebooking()
        self.assertEqual(movie.state, 'prebooking')
        movie.action_start_show()
        self.assertEqual(movie.state, 'ongoing')

        # Create registration
        reg = self.env['movie.registration'].create({
            'partner_id': self.partner.id,
            'movie_id': movie.id,
            'date': self.today,
            'time_slot_id': slot.id,
            'screen_id': screen.id,
            'no_of_tickets': 3,
        })
        self.assertTrue(reg.id)
        reg.write({'state': 'invoiced'})
        self.assertEqual(reg.state, 'invoiced')

        # Verify seats update reflects the booking
        result = self.env['movie.movie'].update_seats(screen.id, slot.id, self.today)
        self.assertEqual(result['available_seats_count'], 25)  # no seats created yet

        # Create seat records for the 3 tickets
        for i in range(3):
            self.env['movie.seats'].create({
                'screen_id': screen.id,
                'time_slot_id': slot.id,
                'movie_registration_id': reg.id,
                'date': self.today,
                'seat': f'A{i + 1}',
                'is_booked': True,
            })
        result2 = self.env['movie.movie'].update_seats(screen.id, slot.id, self.today)
        self.assertEqual(result2['booked_seats_count'], 3)
        self.assertEqual(result2['available_seats_count'], 22)

    def test_cancel_show_blocks_additional_bookings_conceptually(self):
        """Cancelled movie is not returned by ongoing/prebooking search"""
        screen = self.env['movie.screen'].create({
            'name': 'Cancel Screen', 'total_rows': 3, 'no_of_seat_row': 3})
        slot = self.env['time.slots'].search([('movie_time', '=', '23.00')], limit=1) or self.env['time.slots'].create({'movie_time': '23:00'})
        movie = self.env['movie.movie'].create({
            'name': 'To Cancel',
            'release_date': self.today,
            'show_start_date': self.today,
            'show_end_date': self.next_week,
            'available_screens_ids': [(4, screen.id)],
            'available_time_slots_ids': [(4, slot.id)],
            'price': 50.0,
        })
        movie.action_prebooking()
        movie.action_cancel_show()
        self.assertEqual(movie.state, 'cancel')

        active_movies = self.env['movie.movie'].search([
            ('state', 'in', ['ongoing', 'prebooking'])])
        self.assertNotIn(movie, active_movies)
