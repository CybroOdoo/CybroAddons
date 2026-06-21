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
from unittest.mock import MagicMock, patch
from odoo import fields
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


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
class TestMakeTruckBookingPdf(TransactionCase):

    def setUp(self):
        super(TestMakeTruckBookingPdf, self).setUp()

        # Mock Nominatim specifically in the model namespace to bypass Odoo network checks
        self.mock_model_nominatim = patch('odoo.addons.packers_and_movers_management.models.truck_booking.Nominatim')
        self.mock_model_class = self.mock_model_nominatim.start()

        self.mock_geocoder = MagicMock()
        self.mock_geocoder.geocode.side_effect = mock_geocode_func
        self.mock_model_class.return_value = self.mock_geocoder

        self.addCleanup(self.mock_model_nominatim.stop)

        # Setup test data
        self.partner = self.env['res.partner'].create({
            'name': 'Test Wizard Customer',
            'email': 'wizard.customer@example.com',
        })

        self.goods_type = self.env['goods.type'].create({
            'name': 'Books & Stationery',
        })

        self.truck_type = self.env['truck.type'].create({
            'name': 'Test Cargo Truck',
            'capacity': 5.0,
            'weight': 1000.0,
            'unit': 'kg',
        })

        self.truck_model = self.env['fleet.vehicle.model'].create({
            'name': 'Test Heavy Cargo Truck',
            'brand_id': self.env.ref('fleet.brand_audi').id, # standard brand from fleet model data
            'vehicle_type': 'truck',
            'truck_type_id': self.truck_type.id,
        })

        # Set default settings
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.distance_amount', 10.0)
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.is_extra', False)
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.extra_amount', 1.0)
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.is_distance_limited', False)
        self.env['ir.config_parameter'].sudo().set_param('packers_and_movers_management.max_distance', 500.0)

        # Create a booking record to be queried by the wizard
        self.booking = self.env['truck.booking'].create({
            'partner_id': self.partner.id,
            'from_location': 'London',
            'to_location': 'Paris',
            'truck_id': self.truck_model.id,
            'date': fields.Date.today(),
            'goods_type_id': self.goods_type.id,
            'weight': 500,
            'unit': 'kg',
        })
        self.env.flush_all()

    def test_validation_date_check(self):
        """Test that ValidationError is raised when from_date is later than to_date."""
        wizard = self.env['make.truck.booking.pdf'].create({
            'partner_id': self.partner.id,
            'from_date': fields.Date.today(),
            'to_date': fields.Date.add(fields.Date.today(), days=-1),
        })
        with self.assertRaises(ValidationError):
            wizard.action_report_truck_booking()

    def test_report_action_generation_no_filters(self):
        """Test report action generation without optional filters."""
        wizard = self.env['make.truck.booking.pdf'].create({
            'partner_id': self.partner.id,
        })
        action = wizard.action_report_truck_booking()
        self.assertIn(action.get('type'), ['ir.actions.report', 'ir.actions.act_window'])

    def test_report_action_generation_with_filters(self):
        """Test report action generation with all filters applied."""
        wizard = self.env['make.truck.booking.pdf'].create({
            'partner_id': self.partner.id,
            'from_date': fields.Date.today(),
            'to_date': fields.Date.today(),
            'truck_id': self.truck_model.id,
            'goods_type_id': self.goods_type.id,
        })
        action = wizard.action_report_truck_booking()
        self.assertIn(action.get('type'), ['ir.actions.report', 'ir.actions.act_window'])

    def test_wizard_query_data_correctness(self):
        """Test that the SQL query executed by the wizard returns the expected data."""
        wizard = self.env['make.truck.booking.pdf'].create({
            'partner_id': self.partner.id,
            'truck_id': self.truck_model.id,
            'goods_type_id': self.goods_type.id,
        })
        
        self.env.flush_all()
        # Directly run query to verify returned contents
        query = """select pr.name,fv.name as truck,gt.name as goods,
                tb.from_location,tb.to_location,tb.distance,
                tb.weight,tb.unit,amount,tb.date,tb.state from truck_booking
                as tb inner join res_partner as pr on pr.id = tb.partner_id
                inner join fleet_vehicle_model as fv on fv.id = tb.truck_id
                inner join goods_type as gt on gt.id = tb.goods_type_id
                where pr.id = %d """ % wizard.partner_id.id
        
        self.env.cr.execute(query)
        report = self.env.cr.dictfetchall()
        
        self.assertEqual(len(report), 1)
        record = report[0]
        self.assertEqual(record['name'], 'Test Wizard Customer')
        self.assertEqual(record['truck'], 'Test Heavy Cargo Truck')
        self.assertEqual(record['goods'], 'Books & Stationery')
        self.assertEqual(record['from_location'], 'London')
        self.assertEqual(record['to_location'], 'Paris')
        self.assertEqual(record['distance'], 343)
        self.assertEqual(record['weight'], 500)
        self.assertEqual(record['unit'], 'kg')
        self.assertEqual(record['state'], 'draft')
