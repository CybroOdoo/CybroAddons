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
"""Test suite for form_truck_booking_report parser."""
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestFormTruckBookingReport(TransactionCase):
    """Test cases for form_truck_booking_report abstract model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Report Customer'})
        cls.truck_type = cls.env['truck.type'].create({
            'name': 'Container',
            'capacity': 2.0,
            'weight': 3000.0,
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Brand Y'})
        cls.truck = cls.env['fleet.vehicle.model'].create({
            'name': 'Truck Model Y',
            'brand_id': cls.brand.id,
            'vehicle_type': 'truck',
            'truck_type_id': cls.truck_type.id,
        })
        cls.goods_type = cls.env['goods.type'].create({'name': 'Electronics'})
        cls.booking = cls.env['truck.booking'].create({
            'partner_id': cls.partner.id,
            'from_location': 'City A',
            'to_location': 'City B',
            'distance': 75.0,
            'truck_id': cls.truck.id,
            'goods_type_id': cls.goods_type.id,
            'weight': 400,
        })
        cls.report_model = cls.env['report.packers_and_movers_management.form_truck_booking_report']

    def test_get_report_values_with_docids(self):
        """Test generating report values with docids."""
        values = self.report_model._get_report_values([self.booking.id])
        self.assertIn('docs', values)
        self.assertIn('report', values)
        self.assertEqual(len(values['report']), 1)
        self.assertEqual(values['report'][0]['reference_no'], self.booking.reference_no)
        self.assertEqual(values['report'][0]['name'], self.partner.name)
        self.assertEqual(values['report'][0]['distance'], 75.0)

    def test_get_report_values_with_data_fallback(self):
        """Test generating report values with data dictionary booking_ids."""
        values = self.report_model._get_report_values([], data={'booking_ids': [self.booking.id]})
        self.assertEqual(len(values['report']), 1)
        self.assertEqual(values['report'][0]['reference_no'], self.booking.reference_no)

    def test_get_report_values_empty_raises(self):
        """Test generating report values with no IDs raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.report_model._get_report_values([])
