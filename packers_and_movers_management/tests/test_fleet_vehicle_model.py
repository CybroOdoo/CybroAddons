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
"""Test suite for fleet.vehicle.model extension."""
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestFleetVehicleModel(TransactionCase):
    """Test cases for fleet.vehicle.model extension."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Truck Brand'})
        cls.truck_type = cls.env['truck.type'].create({
            'name': 'Medium Truck',
            'capacity': 2.0,
            'weight': 3000.0,
        })

    def test_create_car_model_without_truck_type(self):
        """Test creating a non-truck model without truck_type_id succeeds."""
        model = self.env['fleet.vehicle.model'].create({
            'name': 'Sedan Car',
            'brand_id': self.brand.id,
            'vehicle_type': 'car',
        })
        self.assertEqual(model.name, 'Sedan Car')
        self.assertFalse(model.truck_type_id)

    def test_create_truck_model_with_truck_type(self):
        """Test creating a truck model with truck_type_id succeeds."""
        model = self.env['fleet.vehicle.model'].create({
            'name': 'Eicher Pro 2049',
            'brand_id': self.brand.id,
            'vehicle_type': 'truck',
            'truck_type_id': self.truck_type.id,
        })
        self.assertEqual(model.name, 'Eicher Pro 2049')
        self.assertEqual(model.vehicle_type, 'truck')
        self.assertEqual(model.truck_type_id, self.truck_type)

    def test_create_truck_model_without_truck_type_raises(self):
        """Test creating a truck model without truck_type_id raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.env['fleet.vehicle.model'].create({
                'name': 'Invalid Truck Model',
                'brand_id': self.brand.id,
                'vehicle_type': 'truck',
            })
