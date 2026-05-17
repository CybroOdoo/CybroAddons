# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Prasudhi A (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
from unittest.mock import MagicMock, patch
from datetime import date, timedelta
from odoo.tests.common import TransactionCase
from odoo.addons.fleet_advanced_dashboard.controllers.fleet_advanced_dashboard import FleetFilter


class TestFleetAdvancedDashboard(TransactionCase):
    """Test cases for FleetFilter controller in fleet_advanced_dashboard."""

    @classmethod
    def setUpClass(cls):
        super(TestFleetAdvancedDashboard, cls).setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Dashboard Driver'
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Test Controller Brand'
        })
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Controller Model',
            'brand_id': cls.brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'CTRL-0001',
            'driver_id': cls.partner.id,
        })
        cls.odometer = cls.env['fleet.vehicle.odometer'].create({
            'vehicle_id': cls.vehicle.id,
            'driver_id': cls.partner.id,
            'value': 2000.0,
            'date': date.today() - timedelta(days=10),
        })
        cls.service_type = cls.env['fleet.service.type'].search([], limit=1)
        if not cls.service_type:
            cls.service_type = cls.env['fleet.service.type'].create({
                'name': 'General Service',
                'category': 'service',
            })
        cls.service = cls.env['fleet.vehicle.log.services'].create({
            'vehicle_id': cls.vehicle.id,
            'amount': 300.0,
            'service_type_id': cls.service_type.id,
            'purchaser_id': cls.partner.id,
            'date': date.today() - timedelta(days=10),
        })

    def _make_mock_request(self):
        """Build a MagicMock that behaves like odoo.http.request for this test env."""
        mock_req = MagicMock()
        mock_req.env = self.env
        return mock_req

    def test_fleet_filter_returns_required_keys(self):
        """fleet_filter() must return drivers, vehicles, and manufactures lists."""
        mock_req = self._make_mock_request()
        controller = FleetFilter()

        # Patch using new= to avoid touching the unbound werkzeug LocalProxy
        with patch(
            'odoo.addons.fleet_advanced_dashboard.controllers.fleet_advanced_dashboard.request',
            new=mock_req
        ):
            result = controller.fleet_filter()

        self.assertIsInstance(result, dict)
        self.assertIn('drivers', result)
        self.assertIn('vehicles', result)
        self.assertIn('manufactures', result)

    def test_fleet_filter_includes_created_vehicle_model(self):
        """fleet_filter() vehicles list must include the test vehicle's model."""
        mock_req = self._make_mock_request()
        controller = FleetFilter()

        with patch(
            'odoo.addons.fleet_advanced_dashboard.controllers.fleet_advanced_dashboard.request',
            new=mock_req
        ):
            result = controller.fleet_filter()

        vehicle_ids = [v['id'] for v in result['vehicles']]
        self.assertIn(self.model.id, vehicle_ids,
                      "Test model ID should appear in filter vehicle list")

    def test_fleet_filter_data_no_filters(self):
        """fleet_filter_data() with all-null filters must aggregate all data."""
        mock_req = self._make_mock_request()
        controller = FleetFilter()

        payload = {
            'data': {
                'driver': 'null',
                'vehicle': 'null',
                'manufacturer': 'null',
                'date': 'null',
            }
        }

        with patch(
            'odoo.addons.fleet_advanced_dashboard.controllers.fleet_advanced_dashboard.request',
            new=mock_req
        ):
            result = controller.fleet_filter_data(**payload)

        self.assertIsInstance(result, dict)
        for key in ['total_odometer', 'service_cost', 'recurring_cost',
                    'admin_odometer_list', 'admin_fleet_cost_list',
                    'admin_recurring_list', 'fleet_vehicle_list',
                    'odometer_value_list', 'service_cost_list', 'service_type']:
            self.assertIn(key, result, f"Expected key '{key}' in filter_data result")

        self.assertGreaterEqual(result['total_odometer'], 2000.0)
        self.assertGreaterEqual(result['service_cost'], 300.0)

    def test_fleet_filter_data_with_date_filter(self):
        """fleet_filter_data() with a date filter of 30 days must still capture recent records."""
        mock_req = self._make_mock_request()
        controller = FleetFilter()

        payload = {
            'data': {
                'driver': 'null',
                'vehicle': 'null',
                'manufacturer': 'null',
                'date': '30',   # only records within past 30 days
            }
        }

        with patch(
            'odoo.addons.fleet_advanced_dashboard.controllers.fleet_advanced_dashboard.request',
            new=mock_req
        ):
            result = controller.fleet_filter_data(**payload)

        self.assertIsInstance(result, dict)
        self.assertGreaterEqual(result['total_odometer'], 2000.0,
                                "Odometer records created 10 days ago must be within 30-day filter")
        self.assertGreaterEqual(result['service_cost'], 300.0,
                                "Service records created 10 days ago must be within 30-day filter")

    def test_fleet_filter_data_with_specific_driver(self):
        """fleet_filter_data() filtered by a specific driver should scope the results."""
        mock_req = self._make_mock_request()
        controller = FleetFilter()

        payload = {
            'data': {
                'driver': str(self.partner.id),
                'vehicle': 'null',
                'manufacturer': 'null',
                'date': 'null',
            }
        }

        with patch(
            'odoo.addons.fleet_advanced_dashboard.controllers.fleet_advanced_dashboard.request',
            new=mock_req
        ):
            result = controller.fleet_filter_data(**payload)

        self.assertIsInstance(result, dict)
        self.assertIn('total_odometer', result)
        self.assertIn('service_cost', result)
