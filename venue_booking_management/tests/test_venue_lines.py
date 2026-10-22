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
"""Test cases for venue.lines model."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestVenueLines(TransactionCase):
    """Test suite for venue.lines."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Venue = cls.env['venue']
        cls.VenueLines = cls.env['venue.lines']
        cls.Amenities = cls.env['amenities']
        cls.VenueType = cls.env['venue.type']

        cls.venue_type = cls.VenueType.create({'name': 'Open Lawn'})
        cls.venue = cls.Venue.create({
            'name': 'Green Meadow',
            'venue_type_id': cls.venue_type.id,
            'venue_location': 'Outdoor Area',
        })
        cls.amenity = cls.Amenities.create({
            'name': 'Buffet Table',
            'amount': 25.0,
        })

    def test_create_venue_line_subtotal(self):
        """Test subtotal calculation in venue.lines."""
        line = self.VenueLines.create({
            'venue_id': self.venue.id,
            'amenities_id': self.amenity.id,
            'quantity': 4,
            'status': 'open',
        })
        # 4 * 25.0 = 100.0
        self.assertEqual(line.sub_total, 100.0)
        self.assertEqual(line.amount, 25.0)

        # Update quantity
        line.write({'quantity': 6})
        self.assertEqual(line.sub_total, 150.0)
