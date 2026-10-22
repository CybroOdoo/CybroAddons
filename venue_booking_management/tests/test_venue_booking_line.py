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
"""Test cases for venue.booking.line model."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestVenueBookingLine(TransactionCase):
    """Test suite for venue.booking.line."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Venue = cls.env['venue']
        cls.VenueType = cls.env['venue.type']
        cls.Amenities = cls.env['amenities']
        cls.Partner = cls.env['res.partner']
        cls.VenueBooking = cls.env['venue.booking']
        cls.VenueBookingLine = cls.env['venue.booking.line']

        cls.venue_type = cls.VenueType.create({'name': 'Conference'})
        cls.venue = cls.Venue.create({
            'name': 'Main Hall',
            'venue_type_id': cls.venue_type.id,
            'venue_location': 'Downtown',
        })
        cls.amenity = cls.Amenities.create({
            'name': 'Microphone',
            'amount': 30.0,
        })
        cls.partner = cls.Partner.create({'name': 'Test Client'})

        cls.booking = cls.VenueBooking.create({
            'partner_id': cls.partner.id,
            'venue_id': cls.venue.id,
            'start_date': '2026-11-10 09:00:00',
            'end_date': '2026-11-10 17:00:00',
        })

    def test_booking_line_subtotal(self):
        """Test subtotal computation for extra amenity booking line."""
        line = self.VenueBookingLine.create({
            'venue_booking_id': self.booking.id,
            'amenity_id': self.amenity.id,
            'quantity': 3,
        })
        # 3 * 30.0 = 90.0
        self.assertEqual(line.sub_total, 90.0)
        self.assertEqual(line.state, 'pending')
        self.assertFalse(line.is_invoiced)

        # Update quantity
        line.write({'quantity': 5})
        self.assertEqual(line.sub_total, 150.0)
