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
"""Test cases for venue model."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestVenue(TransactionCase):
    """Test suite for venue model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Venue = cls.env['venue']
        cls.VenueType = cls.env['venue.type']
        cls.Amenities = cls.env['amenities']
        cls.Partner = cls.env['res.partner']

        cls.venue_type = cls.VenueType.create({'name': 'Banquet'})
        cls.amenity1 = cls.Amenities.create({'name': 'Sound System', 'amount': 100.0})
        cls.amenity2 = cls.Amenities.create({'name': 'Stage Lighting', 'amount': 150.0})

        cls.partner = cls.Partner.create({'name': 'Test Client'})

    def test_create_venue_and_computations(self):
        """Test venue creation, subtotal compute, and venue count."""
        venue = self.Venue.create({
            'name': 'Grand Ballroom',
            'venue_type_id': self.venue_type.id,
            'venue_location': '123 Main St, New York',
            'capacity': 300,
            'seating': 250,
            'venue_charge_day': 1000.0,
            'venue_charge_hour': 120.0,
            'additional_charge_day': 50.0,
            'additional_charge_hour': 10.0,
            'venue_line_ids': [
                (0, 0, {'amenities_id': self.amenity1.id, 'quantity': 1}),
                (0, 0, {'amenities_id': self.amenity2.id, 'quantity': 2}),
            ]
        })
        # 1 * 100 + 2 * 150 = 400.0
        self.assertEqual(venue.price_subtotal, 400.0)
        self.assertEqual(venue.venue_count, 0)

        # Create a booking and check venue_count compute
        self.env['venue.booking'].create({
            'partner_id': self.partner.id,
            'venue_id': venue.id,
            'start_date': '2026-11-01 10:00:00',
            'end_date': '2026-11-01 18:00:00',
        })
        venue._compute_venue_count()
        self.assertEqual(venue.venue_count, 1)

    def test_get_venue_type_action(self):
        """Test get_venue_type_action method."""
        venue = self.Venue.create({
            'name': 'Meeting Room A',
            'venue_type_id': self.venue_type.id,
            'venue_location': 'Building 2, Floor 3',
        })
        action = venue.get_venue_type_action()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('domain'), [('venue_id', '=', venue.id)])
        self.assertEqual(action.get('context'), {'default_venue_id': venue.id})
