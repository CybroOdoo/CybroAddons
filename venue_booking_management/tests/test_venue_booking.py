# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test cases for venue.booking model."""
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestVenueBooking(TransactionCase):
    """Test suite for venue.booking."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Venue = cls.env['venue']
        cls.VenueType = cls.env['venue.type']
        cls.Amenities = cls.env['amenities']
        cls.Partner = cls.env['res.partner']
        cls.VenueBooking = cls.env['venue.booking']

        cls.venue_type = cls.VenueType.create({'name': 'Auditorium'})
        cls.included_amenity = cls.Amenities.create({'name': 'Stage', 'amount': 200.0})
        cls.extra_amenity = cls.Amenities.create({'name': 'Podium', 'amount': 50.0})

        cls.venue = cls.Venue.create({
            'name': 'Main Auditorium',
            'venue_type_id': cls.venue_type.id,
            'venue_location': 'Central Plaza',
            'venue_charge_day': 800.0,
            'venue_charge_hour': 100.0,
            'additional_charge_day': 100.0,
            'additional_charge_hour': 20.0,
            'venue_line_ids': [
                (0, 0, {'amenities_id': cls.included_amenity.id, 'quantity': 1})
            ]
        })

        cls.partner = cls.Partner.create({
            'name': 'John Doe',
            'email': 'john@example.com',
        })

    def test_booking_create_and_computes(self):
        """Test creating a booking, sequence, and total calculations."""
        booking = self.VenueBooking.create({
            'partner_id': self.partner.id,
            'venue_id': self.venue.id,
            'booking_type': 'day',
            'start_date': '2026-12-01 09:00:00',
            'end_date': '2026-12-03 18:00:00',
        })
        self.assertTrue(booking.ref)
        self.assertIn(self.partner.name, booking.name)
        self.assertEqual(booking.state, 'draft')
        # Days diff: Dec 1 to Dec 3 = 2 days + 1 = 3 days
        self.assertEqual(booking.days_difference, 3)
        # Booking charge per day = 800 * 3 + additional 100 + venue subtotal (200) = 2700.0
        self.assertEqual(booking.booking_charge, 200.0)
        self.assertEqual(booking.total, (800.0 * 3) + 100.0 + 200.0)

    def test_booking_date_validation(self):
        """Test validation error when start_date >= end_date."""
        with self.assertRaises(UserError):
            self.VenueBooking.create({
                'partner_id': self.partner.id,
                'venue_id': self.venue.id,
                'start_date': '2026-12-05 18:00:00',
                'end_date': '2026-12-05 09:00:00',
            })

    def test_partner_required_validation(self):
        """Test validation when partner is missing."""
        with self.assertRaises(UserError):
            self.VenueBooking.create({
                'partner_id': False,
                'venue_id': self.venue.id,
                'start_date': '2026-12-05 09:00:00',
                'end_date': '2026-12-05 18:00:00',
            })

    def test_duplicate_included_amenity_constraint(self):
        """Test constraint preventing duplicate included amenities."""
        with self.assertRaises(ValidationError):
            self.VenueBooking.create({
                'partner_id': self.partner.id,
                'venue_id': self.venue.id,
                'start_date': '2026-12-10 09:00:00',
                'end_date': '2026-12-10 18:00:00',
                'venue_booking_line_ids': [
                    (0, 0, {'amenity_id': self.included_amenity.id, 'quantity': 1})
                ]
            })

    def test_booking_workflow_and_dates_overlap(self):
        """Test confirm, overlap constraint, cancel, and reset."""
        booking1 = self.VenueBooking.create({
            'partner_id': self.partner.id,
            'venue_id': self.venue.id,
            'start_date': '2026-12-15 09:00:00',
            'end_date': '2026-12-15 18:00:00',
        })
        booking1.action_booking_confirm()
        self.assertEqual(booking1.state, 'confirm')

        # Creating an overlapping booking while booking1 is confirmed should fail with ValidationError
        with self.assertRaises(ValidationError):
            self.VenueBooking.create({
                'partner_id': self.partner.id,
                'venue_id': self.venue.id,
                'start_date': '2026-12-15 10:00:00',
                'end_date': '2026-12-15 14:00:00',
            })

        booking1.action_booking_cancel()
        self.assertEqual(booking1.state, 'cancel')

        booking1.action_reset_to_draft()
        self.assertEqual(booking1.state, 'draft')

        # When booking1 is draft, booking2 can be created and confirmed
        booking2 = self.VenueBooking.create({
            'partner_id': self.partner.id,
            'venue_id': self.venue.id,
            'start_date': '2026-12-15 10:00:00',
            'end_date': '2026-12-15 14:00:00',
        })
        booking2.action_booking_confirm()
        self.assertEqual(booking2.state, 'confirm')

        # Now attempting to confirm booking1 will fail due to overlap with confirmed booking2
        with self.assertRaises(ValidationError):
            booking1.action_booking_confirm()

    def test_invoice_creation_and_close(self):
        """Test invoice creation, view invoice, and close booking."""
        booking = self.VenueBooking.create({
            'partner_id': self.partner.id,
            'venue_id': self.venue.id,
            'start_date': '2026-12-20 09:00:00',
            'end_date': '2026-12-20 18:00:00',
        })
        booking.action_booking_confirm()
        action = booking.action_booking_invoice_create()
        self.assertEqual(booking.state, 'invoice')
        self.assertEqual(booking.invoice_count, 1)

        # Smart button action
        view_action = booking.action_view_invoice()
        self.assertEqual(view_action['res_model'], 'account.move')

        # Close booking
        booking.action_booking_close()
        self.assertEqual(booking.state, 'close')

    def test_ondelete_posted_invoice_protection(self):
        """Test cannot delete a booking with a posted invoice."""
        booking = self.VenueBooking.create({
            'partner_id': self.partner.id,
            'venue_id': self.venue.id,
            'start_date': '2026-12-25 09:00:00',
            'end_date': '2026-12-25 18:00:00',
        })
        booking.action_booking_confirm()
        booking.action_booking_invoice_create()
        invoice = self.env['account.move'].search([('invoice_origin', '=', booking.ref)])
        if invoice:
            invoice.action_post()
            with self.assertRaises(UserError):
                booking.unlink()

    def test_dashboard_queries(self):
        """Test model methods feeding the dashboard."""
        booking = self.VenueBooking.create({
            'partner_id': self.partner.id,
            'venue_id': self.venue.id,
            'start_date': '2026-12-28 09:00:00',
            'end_date': '2026-12-28 18:00:00',
        })
        booking.action_booking_confirm()

        total = self.VenueBooking.get_total_booking()
        self.assertIn('total_booking', total)

        top_venue = self.VenueBooking.get_top_venue()
        self.assertIn('venue', top_venue)

        booking_analysis = self.VenueBooking.get_booking_analysis()
        self.assertIn('name', booking_analysis)

        venue_analysis = self.VenueBooking.get_venue_analysis()
        self.assertIn('name', venue_analysis)

        for option in ['year', 'month', 'week', 'day']:
            filter_data = self.VenueBooking.get_select_filter(option)
            self.assertIn('booking', filter_data)
