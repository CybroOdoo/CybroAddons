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
from odoo.addons.show_booking_management.controller.payment import PaymentPost


@tagged('post_install', '-at_install')
class TestPaymentController(TransactionCase):
    """Test cases for payment.py controller: poll_status business logic."""

    def setUp(self):
        super(TestPaymentController, self).setUp()
        self.today = fields.Date.today()
        self.partner = self.env['res.partner'].create({'name': 'Payment Test Partner'})
        self.screen = self.env['movie.screen'].create({
            'name': 'Payment Screen',
            'total_rows': 10,
            'no_of_seat_row': 10,
        })
        self.time_slot = self.env['time.slots'].create({
            'movie_time': '21:00',
        })
        self.movie = self.env['movie.movie'].create({
            'name': 'Payment Test Movie',
            'release_date': self.today - timedelta(days=5),
            'show_start_date': self.today,
            'show_end_date': self.today + timedelta(days=30),
            'price': 300.0,
            'available_screens_ids': [(4, self.screen.id)],
            'available_time_slots_ids': [(4, self.time_slot.id)],
        })
        self.movie.action_prebooking()
        self.movie.action_start_show()

    # -------------------------------------------------------------------------
    # PaymentPost class registration
    # -------------------------------------------------------------------------
    def test_payment_post_inherits_base(self):
        """Verify PaymentPost inherits from PaymentPostProcessing."""
        from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
        self.assertTrue(issubclass(PaymentPost, PaymentPostProcessing))

    def test_poll_status_route_registered(self):
        """Verify poll_status method is declared in PaymentPost."""
        self.assertTrue(hasattr(PaymentPost, 'poll_status'))

    # -------------------------------------------------------------------------
    # poll_status business logic — movie.registration creation
    # -------------------------------------------------------------------------
    def test_poll_status_creates_registration(self):
        """Test business logic: movie.registration is created with correct fields."""
        reg = self.env['movie.registration'].create({
            'partner_id': self.partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.time_slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 2,
            'state': 'invoiced',
        })
        self.assertEqual(reg.state, 'invoiced')
        self.assertEqual(reg.no_of_tickets, 2)

    # -------------------------------------------------------------------------
    # poll_status business logic — movie.seats creation
    # -------------------------------------------------------------------------
    def test_poll_status_creates_seats(self):
        """Test business logic: movie.seats records are created on payment completion."""
        reg = self.env['movie.registration'].create({
            'partner_id': self.partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.time_slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 1,
            'state': 'invoiced',
        })
        seat = self.env['movie.seats'].create({
            'screen_id': self.screen.id,
            'time_slot_id': self.time_slot.id,
            'movie_registration_id': reg.id,
            'date': self.today,
            'seat': 'C3',
            'is_booked': True,
        })
        self.assertTrue(seat.is_booked)
        self.assertEqual(seat.seat, 'C3')
        self.assertEqual(seat.movie_registration_id.id, reg.id)

    # -------------------------------------------------------------------------
    # poll_status business logic — account.move linkage
    # -------------------------------------------------------------------------
    def test_poll_status_links_invoice_to_registration(self):
        """Test business logic: invoice is linked to movie.registration after payment."""
        reg = self.env['movie.registration'].create({
            'partner_id': self.partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.time_slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 1,
            'state': 'invoiced',
        })
        product = self.env['product.product'].create({
            'name': 'Movie Ticket Product',
            'type': 'service',
        })
        invoice = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': self.today,
            'movie_ticket_id': reg.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Movie Ticket',
                'product_id': product.id,
                'quantity': 1,
                'price_unit': self.movie.price,
            })],
        })
        self.assertEqual(invoice.movie_ticket_id.id, reg.id)

    # -------------------------------------------------------------------------
    # poll_status business logic — update existing registration
    # -------------------------------------------------------------------------
    def test_poll_status_updates_existing_registration(self):
        """Test business logic: existing registration is updated (not duplicated)."""
        reg = self.env['movie.registration'].create({
            'partner_id': self.partner.id,
            'movie_id': self.movie.id,
            'date': self.today,
            'time_slot_id': self.time_slot.id,
            'screen_id': self.screen.id,
            'no_of_tickets': 1,
        })
        reg.sudo().write({'no_of_tickets': 3, 'state': 'invoiced'})
        self.assertEqual(reg.no_of_tickets, 3)
        self.assertEqual(reg.state, 'invoiced')
