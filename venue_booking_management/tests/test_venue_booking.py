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

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
from odoo import fields, Command
from datetime import timedelta


class TestVenueBooking(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test@example.com'
        })
        
        cls.venue_type = cls.env['venue.type'].create({
            'name': 'Test Venue Type'
        })
        
        cls.amenity1 = cls.env['amenities'].create({
            'name': 'Test Amenity 1',
            'price': 50.0
        })
        
        cls.amenity2 = cls.env['amenities'].create({
            'name': 'Test Amenity 2',
            'price': 100.0
        })

        cls.venue = cls.env['venue'].create({
            'name': 'Test Venue',
            'venue_type_id': cls.venue_type.id,
            'venue_location': 'Test Location',
            'capacity': 100,
            'seating': 80,
            'venue_charge_hour': 20.0,
            'venue_charge_day': 200.0,
            'additional_charge_hour': 5.0,
            'additional_charge_day': 50.0,
            'open_time': 8.0,
            'closed_time': 20.0,
            'venue_line_ids': [
                Command.create({
                    'amenities_id': cls.amenity1.id,
                    'quantity': 1,
                })
            ]
        })

    def test_01_venue_price_subtotal_compute(self):
        """Test venue price subtotal computation."""
        self.assertEqual(self.venue.price_subtotal, 50.0)
        self.venue.write({
            'venue_line_ids': [
                Command.create({
                    'amenities_id': self.amenity2.id,
                    'quantity': 2,
                })
            ]
        })
        self.assertEqual(self.venue.price_subtotal, 250.0)

    def test_02_venue_booking_creation_and_computes(self):
        """Test venue booking creation and computations."""
        booking = self.env['venue.booking'].create({
            'partner_id': self.partner.id,
            'venue_id': self.venue.id,
            'start_date': fields.Datetime.now(),
            'end_date': fields.Datetime.now() + timedelta(days=2),
            'booking_type': 'day',
        })
        
        self.assertTrue(booking.ref)
        self.assertEqual(booking.days_difference, 3)
        
        # venue subtotal is 250.0, booking charge day is 200 * 3 = 600, additional charge day is 50.
        # total = 250 + 600 + 50 = 900
        self.assertEqual(booking.booking_charge, 250.0)
        self.assertEqual(booking.total, 900.0)
        
        booking.write({'booking_type': 'hour'})
        # booking charge hour is 20 * 3 = 60, additional charge hour is 5.
        # total = 250 + 60 + 5 = 315
        self.assertEqual(booking.total, 315.0)
        
    def test_03_venue_booking_date_constraints(self):
        """Test venue booking date constraints."""
        with self.assertRaises(UserError):
            self.env['venue.booking'].create({
                'partner_id': self.partner.id,
                'venue_id': self.venue.id,
                'start_date': fields.Datetime.now() + timedelta(days=2),
                'end_date': fields.Datetime.now(),
            })

        booking1 = self.env['venue.booking'].create({
            'partner_id': self.partner.id,
            'venue_id': self.venue.id,
            'start_date': fields.Datetime.now(),
            'end_date': fields.Datetime.now() + timedelta(days=2),
        })
        booking1.action_booking_confirm()
        
        with self.assertRaises(ValidationError):
            self.env['venue.booking'].create({
                'partner_id': self.partner.id,
                'venue_id': self.venue.id,
                'start_date': fields.Datetime.now() + timedelta(days=1),
                'end_date': fields.Datetime.now() + timedelta(days=3),
            })
            
    def test_04_venue_booking_flow(self):
        """Test the booking flow: confirm, invoice, close, cancel."""
        booking = self.env['venue.booking'].create({
            'partner_id': self.partner.id,
            'venue_id': self.venue.id,
            'start_date': fields.Datetime.now() + timedelta(days=10),
            'end_date': fields.Datetime.now() + timedelta(days=12),
            'booking_type': 'day',
        })
        
        booking.action_booking_confirm()
        self.assertEqual(booking.state, 'confirm')
        
        action = booking.action_booking_invoice_create()
        self.assertEqual(booking.state, 'invoice')
        self.assertEqual(action['res_model'], 'account.move')
        
        self.assertEqual(booking.invoice_count, 1)
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.state, 'draft')
        
        with self.assertRaises(ValidationError):
            booking.action_booking_close()
            
        booking.action_booking_cancel()
        self.assertEqual(booking.state, 'cancel')
        
        booking.action_reset_to_draft()
        self.assertEqual(booking.state, 'draft')

    def test_05_amenity_inclusion(self):
        """Test amenity inclusion constraints."""
        booking = self.env['venue.booking'].create({
            'partner_id': self.partner.id,
            'venue_id': self.venue.id,
            'start_date': fields.Datetime.now() + timedelta(days=20),
            'end_date': fields.Datetime.now() + timedelta(days=22),
        })
        
        # This will trigger the _onchange_venue_id implicitly if done via UI,
        # but in test we simulate it.
        booking._onchange_venue_id()
        self.assertTrue(any(line.is_included for line in booking.amenity_line_ids))
