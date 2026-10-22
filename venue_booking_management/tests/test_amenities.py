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
"""Test cases for amenities model."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAmenities(TransactionCase):
    """Test suite for amenities."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Amenities = cls.env['amenities']

    def test_create_amenities(self):
        """Test creating an amenity with amount."""
        amenity = self.Amenities.create({
            'name': 'Projector',
            'amount': 50.0,
        })
        self.assertEqual(amenity.name, 'Projector')
        self.assertEqual(amenity.amount, 50.0)
