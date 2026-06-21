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
from unittest.mock import patch, MagicMock
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


class TestFormTruckBookingReport(common.TransactionCase):

    def setUp(self):
        super(TestFormTruckBookingReport, self).setUp()

        # Mock Nominatim specifically in the model namespace to bypass Odoo network checks
        self.mock_model_nominatim = patch('odoo.addons.packers_and_movers_management.models.truck_booking.Nominatim')
        self.mock_model_class = self.mock_model_nominatim.start()

        self.mock_geocoder = MagicMock()
        self.mock_geocoder.geocode.side_effect = mock_geocode_func
        self.mock_model_class.return_value = self.mock_geocoder

        self.addCleanup(self.mock_model_nominatim.stop)

        # Setup test data
        self.partner = self.env['res.partner'].create({
            'name': 'Test Report Customer',
            'email': 'report.customer@example.com',
        })

        self.goods_type = self.env['goods.type'].create({
            'name': 'Electronics',
        })

        self.truck_type = self.env['truck.type'].create({
            'name': 'Standard Delivery Truck',
            'capacity': 3.0,
            'weight': 800.0,
            'unit': 'kg',
        })

        # Try to use standard fleet brand
        brand_audi = self.env.ref('fleet.brand_audi', raise_if_not_found=False)
        if brand_audi:
            brand_id = brand_audi.id
        else:
            brand = self.env['fleet.vehicle.model.brand'].create({'name': 'Audi'})
            brand_id = brand.id

        self.truck_model = self.env['fleet.vehicle.model'].create({
            'name': 'Test Delivery Truck Model',
            'brand_id': brand_id,
            'vehicle_type': 'truck',
            'truck_type_id': self.truck_type.id,
        })

        # Set default settings
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.distance_amount', 12.0)
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.is_extra', False)
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.extra_amount', 1.0)
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.is_distance_limited', False)
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.max_distance', 500.0)

        # Create a booking record
        self.booking = self.env['truck.booking'].create({
            'partner_id': self.partner.id,
            'from_location': 'London',
            'to_location': 'Paris',
            'truck_id': self.truck_model.id,
            'date': fields.Date.today(),
            'goods_type_id': self.goods_type.id,
            'weight': 400,
            'unit': 'kg',
        })
        self.env.flush_all()

    def test_get_report_values(self):
        """Test that the _get_report_values method retrieves the correct data from the database."""
        report_model = self.env['report.packers_and_movers_management.form_truck_booking_report']
        res = report_model._get_report_values(self.booking.id)

        # Assert returned dictionary structure
        self.assertEqual(res.get('doc_ids'), self.booking.id)
        report_data = res.get('report')
        self.assertTrue(report_data)
        self.assertEqual(len(report_data), 1)

        # Verify query field values correctness
        record = report_data[0]
        self.assertEqual(record['reference_no'], self.booking.reference_no)
        self.assertEqual(record['name'], 'Test Report Customer')
        self.assertEqual(record['truck'], 'Test Delivery Truck Model')
        self.assertEqual(record['goods'], 'Electronics')
        self.assertEqual(record['from_location'], 'London')
        self.assertEqual(record['to_location'], 'Paris')
        self.assertEqual(record['distance'], 343)
        self.assertEqual(record['weight'], 400)
        self.assertEqual(record['unit'], 'kg')
        self.assertEqual(record['amount'], 343 * 12.0)
        self.assertEqual(record['state'], 'draft')

    def test_get_report_values_invalid_id(self):
        """Test that the report returns empty results when an invalid/non-existent ID is passed."""
        report_model = self.env['report.packers_and_movers_management.form_truck_booking_report']
        # Pass a non-existent ID
        res = report_model._get_report_values(999999)
        self.assertEqual(res.get('doc_ids'), 999999)
        self.assertEqual(res.get('report'), [])
