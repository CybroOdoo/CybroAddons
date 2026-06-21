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
from odoo.exceptions import ValidationError
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
    elif location_name == 'Invalid':
        return None
    return MockLocation(10.0, 10.0)


class TestTruckBooking(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestTruckBooking, cls).setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@test.com',
        })

        cls.goods_type = cls.env['goods.type'].create({
            'name': 'Furniture',
        })

        cls.truck_type = cls.env['truck.type'].create({
            'name': 'Large Container',
            'capacity': 5.0,
            'weight': 1000.0,
            'unit': 'kg',
        })

        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Volvo',
        })

        cls.truck_model = cls.env['fleet.vehicle.model'].create({
            'name': 'Volvo FH16',
            'brand_id': cls.brand.id,
            'vehicle_type': 'truck',
            'truck_type_id': cls.truck_type.id,
        })

        # Set default settings
        cls.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.distance_amount', 10.0)
        cls.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.is_extra', False)
        cls.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.extra_amount', 1.0)
        cls.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.is_distance_limited', False)
        cls.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.max_distance', 500.0)

    @patch('geopy.Nominatim.geocode', side_effect=mock_geocode_func)
    def test_booking_creation_and_distance_amount(self, mock_geocode):
        """Test simple booking creation, geocoding distance compute, and price calculation."""
        booking = self.env['truck.booking'].create({
            'partner_id': self.partner.id,
            'from_location': 'London',
            'to_location': 'Paris',
            'truck_id': self.truck_model.id,
            'goods_type_id': self.goods_type.id,
            'weight': 500,
            'date': fields.Date.today(),
        })

        # Ensure order reference sequence is generated
        self.assertNotEqual(booking.reference_no, 'New')
        # Geocode is mocked: London to Paris distance calculations
        self.assertTrue(booking.distance > 0)
        # Expected distance formula based on London & Paris lat/long is around 343km
        self.assertEqual(booking.distance, 343)
        # Standard amount calculation: distance * distance_amount (343 * 10 = 3430)
        self.assertEqual(booking.amount, 3430.0)

    @patch('geopy.Nominatim.geocode', side_effect=mock_geocode_func)
    def test_invalid_locations_raise_validation_error(self, mock_geocode):
        """Test that invalid locations which geocode returns None raise a ValidationError."""
        with self.assertRaises(ValidationError):
            self.env['truck.booking'].create({
                'partner_id': self.partner.id,
                'from_location': 'London',
                'to_location': 'Invalid',
                'truck_id': self.truck_model.id,
                'goods_type_id': self.goods_type.id,
                'weight': 500,
                'date': fields.Date.today(),
            })

    @patch('geopy.Nominatim.geocode', side_effect=mock_geocode_func)
    def test_distance_limit_constraints(self, mock_geocode):
        """Test constraints limit validation."""
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.is_distance_limited', True)
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.max_distance', 100.0)

        # London to Paris is ~343km which exceeds 100km max distance limit.
        with self.assertRaises(ValidationError):
            self.env['truck.booking'].create({
                'partner_id': self.partner.id,
                'from_location': 'London',
                'to_location': 'Paris',
                'truck_id': self.truck_model.id,
                'goods_type_id': self.goods_type.id,
                'weight': 500,
                'date': fields.Date.today(),
            })

        # Inside limit works
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.max_distance', 400.0)
        booking = self.env['truck.booking'].create({
            'partner_id': self.partner.id,
            'from_location': 'London',
            'to_location': 'Paris',
            'truck_id': self.truck_model.id,
            'goods_type_id': self.goods_type.id,
            'weight': 500,
            'date': fields.Date.today(),
        })
        self.assertEqual(booking.distance, 343)

    @patch('geopy.Nominatim.geocode', side_effect=mock_geocode_func)
    def test_extra_amount_multiplier(self, mock_geocode):
        """Test amount calculation when is_extra is enabled."""
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.is_extra', True)
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.extra_amount', 1.5)

        booking = self.env['truck.booking'].create({
            'partner_id': self.partner.id,
            'from_location': 'London',
            'to_location': 'Paris',
            'truck_id': self.truck_model.id,
            'goods_type_id': self.goods_type.id,
            'weight': 500,
            'date': fields.Date.today(),
        })

        # Expected calculation: distance * distance_amount * extra_amount (343 * 10 * 1.5 = 5145.0)
        self.assertEqual(booking.amount, 5145.0)

    @patch('geopy.Nominatim.geocode', side_effect=mock_geocode_func)
    def test_date_validation(self, mock_geocode):
        """Test validation preventing bookings set in the past."""
        booking = self.env['truck.booking'].new({
            'partner_id': self.partner.id,
            'from_location': 'London',
            'to_location': 'Paris',
            'truck_id': self.truck_model.id,
            'goods_type_id': self.goods_type.id,
            'weight': 500,
            'date': fields.Date.add(fields.Date.today(), days=-2),
        })
        with self.assertRaises(ValidationError):
            booking._onchange_date()

    @patch('geopy.Nominatim.geocode', side_effect=mock_geocode_func)
    def test_state_transitions_and_invoice_creation(self, mock_geocode):
        """Test action_confirm, invoice creation, and invoice tracking functions."""
        booking = self.env['truck.booking'].create({
            'partner_id': self.partner.id,
            'from_location': 'London',
            'to_location': 'Paris',
            'truck_id': self.truck_model.id,
            'goods_type_id': self.goods_type.id,
            'weight': 500,
            'date': fields.Date.today(),
        })

        self.assertEqual(booking.state, 'draft')
        booking.action_confirm()
        self.assertEqual(booking.state, 'confirm')

        # Create Invoice
        action = booking.action_create_invoice()
        self.assertEqual(action['res_model'], 'account.move')
        self.assertEqual(booking.invoice_count, 1)

        # Smart button action
        view_action = booking.action_view_invoice()
        self.assertEqual(view_action['res_model'], 'account.move')
        self.assertEqual(view_action['domain'], [('invoice_origin', '=', booking.reference_no)])

    @patch('geopy.Nominatim.geocode', side_effect=mock_geocode_func)
    def test_dashboard_methods(self, mock_geocode):
        """Test dashboard query analysis methods."""
        booking = self.env['truck.booking'].create({
            'partner_id': self.partner.id,
            'from_location': 'London',
            'to_location': 'Paris',
            'truck_id': self.truck_model.id,
            'goods_type_id': self.goods_type.id,
            'weight': 500,
            'date': fields.Date.today(),
        })

        # Test get_total_booking
        totals = self.env['truck.booking'].get_total_booking()
        self.assertEqual(totals['total_booking'], 1)
        self.assertEqual(totals['total_distance_count'], 343)
        self.assertEqual(totals['total_amount'], 3430.0)

        # Test get_top_truck
        top = self.env['truck.booking'].get_top_truck()
        self.assertEqual(len(top['truck']), 1)
        self.assertEqual(top['truck'][0]['name'], 'Volvo FH16')

        # Test analyses
        booking_analysis = self.env['truck.booking'].get_booking_analysis()
        self.assertIn('Test Customer', booking_analysis['name'])

        truck_analysis = self.env['truck.booking'].get_truck_analysis()
        self.assertIn('Volvo FH16', truck_analysis['name'])

        distance = self.env['truck.booking'].get_distance()
        self.assertIn('Test Customer', distance['cust'])
        self.assertIn('Volvo FH16', distance['truck_name'])

        weight = self.env['truck.booking'].get_weight()
        self.assertIn('Test Customer', weight['cust'])
        self.assertIn('Volvo FH16', weight['truck_name'])

        # Test get_select_filter
        filters = self.env['truck.booking'].get_select_filter('year')
        self.assertTrue(len(filters) > 0)
        self.assertEqual(filters['booking'][0]['count'], 1)

    def test_wizard_report(self):
        """Test that the make.truck.booking.pdf wizard enforces validations and runs query successfully."""
        wizard = self.env['make.truck.booking.pdf'].create({
            'from_date': fields.Date.today(),
            'to_date': fields.Date.add(fields.Date.today(), days=-1),
            'partner_id': self.partner.id,
        })
        with self.assertRaises(ValidationError):
            wizard.action_report_truck_booking()

        # Valid dates
        wizard.write({
            'to_date': fields.Date.add(fields.Date.today(), days=5),
        })
        action = wizard.action_report_truck_booking()
        self.assertIn(action.get('type'), ['ir.actions.report', 'ir.actions.act_window'])
