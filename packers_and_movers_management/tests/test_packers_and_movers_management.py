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
import json
from unittest.mock import patch, MagicMock
from odoo.tests import tagged, HttpCase
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


@tagged('post_install', '-at_install')
class TestPackersAndMoversManagementController(HttpCase):

    def setUp(self):
        super(TestPackersAndMoversManagementController, self).setUp()

        # Mock Nominatim specifically in the controller and model namespaces to bypass Odoo sandbox network checks
        self.mock_controller_nominatim = patch('odoo.addons.packers_and_movers_management.controllers.packers_and_movers_management.Nominatim')
        self.mock_model_nominatim = patch('odoo.addons.packers_and_movers_management.models.truck_booking.Nominatim')
        
        self.mock_ctrl_class = self.mock_controller_nominatim.start()
        self.mock_model_class = self.mock_model_nominatim.start()

        self.mock_geocoder = MagicMock()
        self.mock_geocoder.geocode.side_effect = mock_geocode_func

        self.mock_ctrl_class.return_value = self.mock_geocoder
        self.mock_model_class.return_value = self.mock_geocoder

        self.addCleanup(self.mock_controller_nominatim.stop)
        self.addCleanup(self.mock_model_nominatim.stop)

        # Setup test data
        self.country = self.env['res.country'].search([('code', '=', 'GB')], limit=1)
        if not self.country:
            self.country = self.env['res.country'].create({
                'name': 'United Kingdom Test',
                'code': 'GB',
            })

        self.state = self.env['res.country.state'].search([('code', '=', 'LDN'), ('country_id', '=', self.country.id)], limit=1)
        if not self.state:
            self.state = self.env['res.country.state'].create({
                'name': 'Greater London',
                'code': 'LDN',
                'country_id': self.country.id,
            })

        self.goods_type = self.env['goods.type'].create({
            'name': 'Office Equipment',
        })

        self.truck_type = self.env['truck.type'].create({
            'name': 'Small Van',
            'capacity': 1.5,
            'weight': 300.0,
            'unit': 'kg',
        })

        self.brand = self.env['fleet.vehicle.model.brand'].create({
            'name': 'Ford',
        })

        self.truck_model = self.env['fleet.vehicle.model'].create({
            'name': 'Ford Transit',
            'brand_id': self.brand.id,
            'vehicle_type': 'truck',
            'truck_type_id': self.truck_type.id,
        })

    def test_booking_page_rendering(self):
        """Test GET /booking renders successfully."""
        response = self.url_open('/booking')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ford Transit', response.content)
        self.assertIn(b'Office Equipment', response.content)

    def test_goods_page_rendering(self):
        """Test GET /goods renders successfully."""
        response = self.url_open('/goods')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Office Equipment', response.content)

    def test_truck_page_rendering(self):
        """Test GET /truck renders successfully."""
        response = self.url_open('/truck')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Small Van', response.content)

    def test_booking_submission(self):
        """Test POST/GET /booking/submit creates partner/booking and redirects to success page."""
        post_data = {
            'name': 'John Doe',
            'city': 'London',
            'state': self.state.id,
            'country': self.country.id,
            'pickup_location': 'London',
            'drop_location': 'Paris',
            'truck_type': self.truck_model.id,
            'date': fields.Date.today(),
            'goods_type': self.goods_type.id,
            'weight': 150,
            'unit': 'kg',
        }
        
        # Use GET query arguments to bypass CSRF token requirement
        from urllib.parse import urlencode
        query_string = urlencode(post_data)
        response = self.url_open(f'/booking/submit?{query_string}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Booking have been Created Successfully.', response.content)

        # Verify records are created in DB
        partner = self.env['res.partner'].search([('name', '=', 'John Doe')], limit=1)
        self.assertTrue(partner.exists())
        self.assertEqual(partner.city, 'London')

        booking = self.env['truck.booking'].search([('partner_id', '=', partner.id)], limit=1)
        self.assertTrue(booking.exists())
        self.assertEqual(booking.from_location, 'London')
        self.assertEqual(booking.to_location, 'Paris')
        self.assertEqual(booking.distance, 343)

    def test_geo_location_json_endpoint(self):
        """Test /geo/<from_location>/<to_location> json endpoint returns expected distance."""
        # JSON endpoint in Odoo is accessed via POST with json-rpc format:
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {},
            'id': 1
        }
        response = self.url_open('/geo/London/Paris', data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200)
        
        resp_data = json.loads(response.content)
        self.assertIn('result', resp_data)
        self.assertEqual(resp_data['result'], 343)
