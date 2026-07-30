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
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase


class TestPaymentPostProcessing(TransactionCase):
    """
    Tests for payment post-processing logic.
    We test the model-level operations that poll_status triggers rather than
    the HTTP layer (which requires a live payment provider).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = date.today()
        cls.next_week = cls.today + timedelta(days=7)

        cls.screen = cls.env['movie.screen'].create({
            'name': 'Payment Screen', 'total_rows': 10, 'no_of_seat_row': 10})
        cls.slot = cls.env['time.slots'].search([('movie_time', '=', '16.00')], limit=1) or cls.env['time.slots'].create({'movie_time': '16:00'})
        cls.partner = cls.env['res.partner'].create({'name': 'Payment Partner'})
        cls.movie = cls.env['movie.movie'].create({
            'name': 'Payment Test Movie',
            'release_date': cls.today,
            'show_start_date': cls.today,
            'show_end_date': cls.next_week,
            'price': 250.0,
            'state': 'ongoing',
            'available_screens_ids': [(4, cls.screen.id)],
            'available_time_slots_ids': [(4, cls.slot.id)],
        })

    # ── Helper ────────────────────────────────────────────────────────────────

    def _create_draft_registration(self, tickets=2):
        return self.env['movie.registration'].create({
            'partner_id': self.partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': tickets,
        })

    def _create_invoice(self, quantity=2):
        product = self.env['product.product'].create({
            'name': 'Movie Ticket', 'type': 'service'})
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Ticket',
                'product_id': product.id,
                'quantity': quantity,
                'price_unit': self.movie.price,
            })],
        })
        invoice.action_post()
        return invoice

    # ── Registration state after payment ──────────────────────────────────────

    def test_registration_state_updated_to_invoiced(self):
        """Simulates payment completion by writing 'invoiced' state"""
        reg = self._create_draft_registration()
        self.assertEqual(reg.state, 'draft')
        reg.write({'state': 'invoiced'})
        self.assertEqual(reg.state, 'invoiced')

    def test_seat_records_created_after_payment(self):
        """Seat records are linked to registration with is_booked=True"""
        reg = self._create_draft_registration(tickets=3)
        selected_seats = ['A1', 'A2', 'A3']
        for seat in selected_seats:
            self.env['movie.seats'].create({
                'screen_id': self.screen.id,
                'time_slot_id': self.slot.id,
                'movie_registration_id': reg.id,
                'date': self.today,
                'seat': seat,
                'is_booked': True,
            })
        reg.write({
            'no_of_tickets': 3,
            'state': 'invoiced',
        })
        self.assertEqual(len(reg.seat_ids), 3)
        self.assertTrue(all(s.is_booked for s in reg.seat_ids))
        self.assertEqual(sorted(reg.seat_ids.mapped('seat')), ['A1', 'A2', 'A3'])

    def test_invoice_linked_to_registration(self):
        """account.move.movie_ticket_id is set to the registration after payment"""
        reg = self._create_draft_registration()
        invoice = self._create_invoice()
        invoice.write({'movie_ticket_id': reg.id})
        self.assertEqual(invoice.movie_ticket_id, reg)

    def test_existing_registration_seats_replaced_on_resubmit(self):
        """On re-booking, old seats are unlinked and new ones are created"""
        reg = self._create_draft_registration(tickets=2)
        # Create initial seats
        old_seats = self.env['movie.seats'].create([
            {'screen_id': self.screen.id, 'time_slot_id': self.slot.id,
             'movie_registration_id': reg.id, 'date': self.today,
             'seat': 'Z1', 'is_booked': True},
            {'screen_id': self.screen.id, 'time_slot_id': self.slot.id,
             'movie_registration_id': reg.id, 'date': self.today,
             'seat': 'Z2', 'is_booked': True},
        ])
        self.assertEqual(len(reg.seat_ids), 2)

        # Simulate re-booking: delete old seats, create new ones
        reg.seat_ids.unlink()
        self.assertEqual(len(reg.seat_ids), 0)

        self.env['movie.seats'].create([
            {'screen_id': self.screen.id, 'time_slot_id': self.slot.id,
             'movie_registration_id': reg.id, 'date': self.today,
             'seat': 'B1', 'is_booked': True},
        ])
        reg.write({'no_of_tickets': 1})
        self.assertEqual(len(reg.seat_ids), 1)
        self.assertEqual(reg.seat_ids[0].seat, 'B1')

    # ── QR code generation ────────────────────────────────────────────────────

    def test_get_qr_code_image_returns_bytes(self):
        """get_qr_code_image generates a non-empty base64 image"""
        reg = self._create_draft_registration(tickets=1)
        # Add one seat so get_qr_code_image has data
        self.env['movie.seats'].create({
            'screen_id': self.screen.id,
            'time_slot_id': self.slot.id,
            'movie_registration_id': reg.id,
            'date': self.today,
            'seat': 'D4',
            'is_booked': True,
        })
        reg.write({'no_of_tickets': 1})
        qr = reg.get_qr_code_image()
        self.assertTrue(qr)
        # Must be valid base64
        import base64
        decoded = base64.b64decode(qr)
        self.assertTrue(decoded.startswith(b'\x89PNG'))  # PNG magic bytes

    # ── Seat availability after invoiced bookings ─────────────────────────────

    def test_booked_seats_reduce_availability(self):
        """Invoiced registrations reduce available seats in check_seat_available"""
        reg = self._create_draft_registration(tickets=5)
        reg.write({'state': 'invoiced'})

        result = self.env['movie.registration'].check_seat_available(
            self.today, self.slot.id, self.screen.id, 96)
        self.assertEqual(result['Status'], 'Failed')

        result_ok = self.env['movie.registration'].check_seat_available(
            self.today, self.slot.id, self.screen.id, 95)
        self.assertEqual(result_ok['Status'], 'Success')

    def test_seats_on_different_date_do_not_affect_count(self):
        """Bookings on a different date do not reduce seats for today"""
        tomorrow = self.today + timedelta(days=1)
        reg = self._create_draft_registration(tickets=10)
        # Write a different date directly to simulate a tomorrow booking
        reg.write({'date': tomorrow, 'state': 'invoiced'})

        result = self.env['movie.registration'].check_seat_available(
            self.today, self.slot.id, self.screen.id, 100)
        self.assertEqual(result['Status'], 'Success')
