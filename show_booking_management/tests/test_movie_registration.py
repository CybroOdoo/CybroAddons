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
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestMovieRegistration(TransactionCase):
    """Test cases for movie.registration model functions."""

    def setUp(self):
        super(TestMovieRegistration, self).setUp()
        self.today = fields.Date.today()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.screen = self.env['movie.screen'].create({
            'name': 'Screen B',
            'total_rows': 10,
            'no_of_seat_row': 10,
        })
        self.time_slot = self.env['time.slots'].create({
            'movie_time': '18:00',
        })
        self.movie = self.env['movie.movie'].create({
            'name': 'Test Reg Movie',
            'release_date': self.today - timedelta(days=10),
            'show_start_date': self.today,
            'show_end_date': self.today + timedelta(days=30),
            'price': 200.0,
            'available_screens_ids': [(4, self.screen.id)],
            'available_time_slots_ids': [(4, self.time_slot.id)],
            'prebooking_slot': 50,
        })
        self.movie.action_prebooking()
        self.movie.action_start_show()
        self.registration = self.env['movie.registration'].create({
            'partner_id': self.partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.time_slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 2,
        })

    # -------------------------------------------------------------------------
    # create (sequence assignment)
    # -------------------------------------------------------------------------
    def test_create_assigns_sequence(self):
        """Test create assigns a sequence number (not 'New')."""
        self.assertNotEqual(self.registration.name, 'New')
        self.assertTrue(self.registration.name)

    # -------------------------------------------------------------------------
    # _compute_available_time_slot_ids
    # -------------------------------------------------------------------------
    def test_compute_available_time_slot_ids(self):
        """Test time slots and screens are computed from the selected movie."""
        self.registration._compute_available_time_slot_ids()
        self.assertIn(self.time_slot.id,
                      self.registration.available_time_slot_ids.ids)
        self.assertIn(self.screen.id,
                      self.registration.available_screens_ids.ids)

    # -------------------------------------------------------------------------
    # check_seat_availability
    # -------------------------------------------------------------------------
    def test_check_seat_availability_valid(self):
        """Test no error when seats are available."""
        try:
            self.registration.check_seat_availability()
        except ValidationError:
            self.fail("check_seat_availability raised ValidationError unexpectedly")

    def test_check_seat_availability_full(self):
        """Test ValidationError when seats exceed total_seat_count."""
        with self.assertRaises(ValidationError):
            self.registration.write({'no_of_tickets': self.screen.total_seat_count + 1})

    # -------------------------------------------------------------------------
    # check_seat (constraint)
    # -------------------------------------------------------------------------
    def test_check_seat_zero_tickets(self):
        """Test ValidationError when no_of_tickets is 0 or negative."""
        with self.assertRaises(ValidationError):
            self.registration.no_of_tickets = 0
            self.registration.check_seat()

    # -------------------------------------------------------------------------
    # set_values (onchange)
    # -------------------------------------------------------------------------
    def test_set_values(self):
        """Test set_values clears time_slot_id and screen_id."""
        self.registration.set_values()
        self.assertFalse(self.registration.time_slot_id)
        self.assertFalse(self.registration.screen_id)

    # -------------------------------------------------------------------------
    # action_select_seats
    # -------------------------------------------------------------------------
    def test_action_select_seats(self):
        """Test action_select_seats returns act_url action with correct URL."""
        result = self.registration.action_select_seats()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')
        self.assertIn('/movie/book_ticket', result.get('url', ''))

    def test_action_select_seats_missing_fields(self):
        """Test action_select_seats raises ValidationError if required fields missing."""
        reg = self.env['movie.registration'].new({
            'date': self.today,
            'time_slot_id': self.time_slot.id,
            'screen_id': self.screen.id,
        })
        with self.assertRaises(ValidationError):
            reg.action_select_seats()

    # -------------------------------------------------------------------------
    # action_generate_ticket_pdf
    # -------------------------------------------------------------------------
    def test_action_generate_ticket_pdf(self):
        """Test action_generate_ticket_pdf returns a report action dict."""
        action = self.registration.action_generate_ticket_pdf()
        self.assertIsInstance(action, dict)
        self.assertIn(action.get('type'), [
            'ir.actions.report', 'ir.actions.act_window'])

    # -------------------------------------------------------------------------
    # get_qr_code_image
    # -------------------------------------------------------------------------
    def test_get_qr_code_image(self):
        """Test get_qr_code_image returns base64-encoded bytes."""
        # Create a seat to avoid empty seat list in QR data
        self.env['movie.seats'].create({
            'screen_id': self.screen.id,
            'time_slot_id': self.time_slot.id,
            'movie_registration_id': self.registration.id,
            'date': self.today,
            'seat': 'A1',
            'is_booked': True,
        })
        qr_data = self.registration.get_qr_code_image()
        self.assertTrue(qr_data)

    # -------------------------------------------------------------------------
    # check_seat_available (model method for website)
    # -------------------------------------------------------------------------
    def test_check_seat_available_success(self):
        """Test check_seat_available returns Success when seats are free."""
        result = self.env['movie.registration'].check_seat_available(
            str(self.today), self.time_slot.id, self.screen.id, 1
        )
        self.assertEqual(result.get('Status'), 'Success')

    def test_check_seat_available_over_capacity(self):
        """Test check_seat_available returns Failed when over capacity."""
        result = self.env['movie.registration'].check_seat_available(
            str(self.today), self.time_slot.id, self.screen.id,
            self.screen.total_seat_count + 10
        )
        self.assertEqual(result.get('Status'), 'Failed')

    # -------------------------------------------------------------------------
    # action_open_invoices
    # -------------------------------------------------------------------------
    def test_action_open_invoices(self):
        """Test action_open_invoices returns act_window with correct domain."""
        result = self.registration.action_open_invoices()
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
        self.assertEqual(result.get('res_model'), 'account.move')
        self.assertIn(('movie_ticket_id', '=', self.registration.id),
                      result.get('domain', []))
