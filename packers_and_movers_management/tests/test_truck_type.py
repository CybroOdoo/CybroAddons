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
"""Test suite for truck.type model."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestTruckType(TransactionCase):
    """Test cases for the truck.type model."""

    def test_create_truck_type(self):
        """Test creating a truck type and verify dimensions and capacity."""
        truck_type = self.env['truck.type'].create({
            'name': '14 Ft Container',
            'length': 14.0,
            'width': 6.0,
            'height': 6.5,
            'capacity': 2.0,
            'weight': 3500.0,
            'unit': 'kg',
        })
        self.assertEqual(truck_type.name, '14 Ft Container')
        self.assertEqual(truck_type.length, 14.0)
        self.assertEqual(truck_type.width, 6.0)
        self.assertEqual(truck_type.height, 6.5)
        self.assertEqual(truck_type.capacity, 2.0)
        self.assertEqual(truck_type.weight, 3500.0)
        self.assertEqual(truck_type.unit, 'kg')
        self.assertEqual(truck_type.company_id, self.env.company)

    def test_truck_type_unit_selection(self):
        """Test creating truck type with tons unit."""
        truck_type = self.env['truck.type'].create({
            'name': 'Heavy 20 Ft Truck',
            'capacity': 3.0,
            'weight': 10.0,
            'unit': 'tons',
        })
        self.assertEqual(truck_type.unit, 'tons')
