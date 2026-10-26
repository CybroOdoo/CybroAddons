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
"""Test suite for truck_booking_report parser."""
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestTruckBookingReport(TransactionCase):
    """Test cases for truck_booking_report abstract model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Report Customer 2'})
        cls.truck_type = cls.env['truck.type'].create({
            'name': 'Container Z',
            'capacity': 2.0,
            'weight': 3000.0,
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Brand Z'})
        cls.truck = cls.env['fleet.vehicle.model'].create({
            'name': 'Truck Model Z',
            'brand_id': cls.brand.id,
            'vehicle_type': 'truck',
            'truck_type_id': cls.truck_type.id,
        })
        cls.goods_type = cls.env['goods.type'].create({'name': 'Machinery'})
        cls.booking = cls.env['truck.booking'].create({
            'partner_id': cls.partner.id,
            'from_location': 'City X',
            'to_location': 'City Y',
            'distance': 120.0,
            'truck_id': cls.truck.id,
            'goods_type_id': cls.goods_type.id,
            'weight': 600,
        })
        cls.report_model = cls.env['report.packers_and_movers_management.report_truck_booking']

    def test_get_report_values_with_docids(self):
        """Test report values extraction with docids."""
        values = self.report_model._get_report_values([self.booking.id])
        self.assertIn('docs', values)
        self.assertIn('report', values)
        self.assertEqual(len(values['report']), 1)
        self.assertEqual(values['report'][0]['reference_no'], self.booking.reference_no)
        self.assertEqual(values['report'][0]['goods'], self.goods_type.name)

    def test_get_report_values_with_data_dict(self):
        """Test report values extraction with passed data dictionary."""
        precomputed_report = [{'reference_no': 'TB-001', 'name': 'Partner A'}]
        values = self.report_model._get_report_values([], data={'report': precomputed_report})
        self.assertEqual(values['report'], precomputed_report)

    def test_get_report_values_empty_raises(self):
        """Test report values generation with no data raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.report_model._get_report_values([], data={})
