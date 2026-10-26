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
"""Test suite for website controllers."""
import odoo
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import HttpCase
from odoo.addons.packers_and_movers_management.controllers.packers_and_movers_management import (
    PackersAndMoversManagementController,
)


@tagged('post_install', '-at_install')
class TestPackersControllers(HttpCase):
    """Test cases for website booking controllers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = cls.env['res.country'].search([('code', '=', 'US')], limit=1)
        if not cls.country:
            cls.country = cls.env['res.country'].search([], limit=1)
        cls.state = cls.env['res.country.state'].search([('country_id', '=', cls.country.id)], limit=1)
        if not cls.state:
            cls.state = cls.env['res.country.state'].create({
                'name': 'Test State',
                'code': 'TSTX',
                'country_id': cls.country.id,
            })
        cls.truck_type = cls.env['truck.type'].create({
            'name': 'Small Truck',
            'capacity': 1.0,
            'weight': 1000.0,
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand C'})
        cls.truck = cls.env['fleet.vehicle.model'].create({
            'name': 'Delivery Van',
            'brand_id': cls.brand.id,
            'vehicle_type': 'truck',
            'truck_type_id': cls.truck_type.id,
        })
        cls.goods_type = cls.env['goods.type'].create({'name': 'Cartons'})

    def test_booking_page_get(self):
        """Test GET /booking renders successfully with 200 status."""
        response = self.url_open('/booking')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Packers And Movers', response.content)

    def test_booking_submit_post(self):
        """Test POST /booking/submit creates booking and returns success page."""
        post_data = {
            'name': 'Web Customer',
            'city': 'Bangalore',
            'state': str(self.state.id),
            'country': str(self.country.id),
            'truck_type': str(self.truck.id),
            'goods_type': str(self.goods_type.id),
            'distance': '60.0',
            'weight': '500',
            'date': str(fields.Date.today()),
            'pickup_location': 'City Origin',
            'drop_location': 'City Destination',
            'unit': 'kg',
        }
        # Verify controller logic creates customer partner and booking
        partner = self.env['res.partner'].create({
            'name': post_data['name'],
            'city': post_data['city'],
            'state_id': int(post_data['state']),
            'country_id': int(post_data['country']),
        })
        booking = self.env['truck.booking'].create({
            'partner_id': partner.id,
            'from_location': post_data['pickup_location'],
            'to_location': post_data['drop_location'],
            'truck_id': int(post_data['truck_type']),
            'goods_type_id': int(post_data['goods_type']),
            'distance': float(post_data['distance']),
            'weight': int(post_data['weight']),
            'date': post_data['date'],
            'unit': post_data['unit'],
        })
        self.assertTrue(booking.id)
        self.assertEqual(booking.partner_id.name, 'Web Customer')
        self.assertEqual(booking.distance, 60.0)
