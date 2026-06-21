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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch
from odoo.tests import common
from odoo import fields


class MockLocation:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude


def mock_geocode_func(location_name):
    if location_name == 'London':
        return MockLocation(51.5074, -0.1278)
    elif location_name == 'Paris':
        return MockLocation(48.8566, 2.3522)
    return MockLocation(10.0, 10.0)


class TestAccountMove(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountMove, cls).setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Account Test Customer',
            'email': 'account_customer@test.com',
        })

        cls.goods_type = cls.env['goods.type'].create({
            'name': 'Boxes',
        })

        cls.truck_type = cls.env['truck.type'].create({
            'name': 'Medium Container',
            'capacity': 3.0,
            'weight': 500.0,
            'unit': 'kg',
        })

        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Scania',
        })

        cls.truck_model = cls.env['fleet.vehicle.model'].create({
            'name': 'Scania R500',
            'brand_id': cls.brand.id,
            'vehicle_type': 'truck',
            'truck_type_id': cls.truck_type.id,
        })

        cls.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.distance_amount', 12.0)

    @patch('geopy.Nominatim.geocode', side_effect=mock_geocode_func)
    def test_action_post(self, mock_geocode):
        """Test that posting an invoice linked to a booking sets the booking state to 'invoice'."""
        booking = self.env['truck.booking'].create({
            'partner_id': self.partner.id,
            'from_location': 'London',
            'to_location': 'Paris',
            'truck_id': self.truck_model.id,
            'goods_type_id': self.goods_type.id,
            'weight': 100,
            'date': fields.Date.today(),
        })

        booking.action_confirm()
        self.assertEqual(booking.state, 'confirm')

        # Create the invoice via action_create_invoice
        action = booking.action_create_invoice()
        invoice_id = action['res_id']
        invoice = self.env['account.move'].browse(invoice_id)
        self.assertEqual(invoice.state, 'draft')

        # Post the invoice.
        # Note: If the test environment lacks a full tax/journal configuration,
        # we can mock any potential errors or simply trigger action_post().
        invoice.action_post()

        # Check booking state is updated
        self.assertEqual(invoice.state, 'posted')
        self.assertEqual(booking.state, 'invoice')
