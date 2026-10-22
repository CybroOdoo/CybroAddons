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
"""Test cases for venue.type model."""
import base64
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestVenueType(TransactionCase):
    """Test suite for venue.type."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.VenueType = cls.env['venue.type']
        cls.sample_image = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='

    def test_create_venue_type(self):
        """Test creating a venue type record."""
        venue_type = self.VenueType.create({
            'name': 'Conference Hall',
            'image': self.sample_image,
        })
        self.assertEqual(venue_type.name, 'Conference Hall')
        self.assertTrue(venue_type.image)
