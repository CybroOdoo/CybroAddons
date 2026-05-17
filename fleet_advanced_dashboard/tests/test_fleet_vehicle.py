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
from odoo.tests.common import TransactionCase
from datetime import date, timedelta


class TestFleetVehicle(TransactionCase):
    """Test cases for FleetVehicle model methods in fleet_advanced_dashboard."""

    @classmethod
    def setUpClass(cls):
        super(TestFleetVehicle, cls).setUpClass()

        # Create fleet manager user using group_ids (Odoo 19)
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Fleet Manager Test',
            'login': 'fleet_manager_test_v19',
            'group_ids': [(6, 0, [cls.env.ref('fleet.fleet_group_manager').id])]
        })

        # Create a Fleet Officer user (non-manager) — needs fleet_group_user to
        # read fleet.vehicle.odometer records, but NOT fleet_group_manager so
        # get_tiles_data() still returns flag=0.
        cls.normal_user = cls.env['res.users'].create({
            'name': 'Fleet Normal User Test',
            'login': 'fleet_user_test_v19',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('fleet.fleet_group_user').id,
            ])]
        })

        # Brand and model
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Test Brand Dashboard'
        })
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Model Dashboard',
            'brand_id': cls.brand.id
        })

        # Vehicle assigned to the normal user as manager
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'TEST-DASH-001',
            'manager_id': cls.normal_user.id,
        })

        # Odometer reading (within last 30 days so graph catches it)
        cls.odometer = cls.env['fleet.vehicle.odometer'].create({
            'vehicle_id': cls.vehicle.id,
            'value': 1500.0,
            'date': date.today() - timedelta(days=15),
        })

        # Service type and log
        cls.service_type = cls.env['fleet.service.type'].create({
            'name': 'Test Oil Change',
            'category': 'service',
        })
        cls.service = cls.env['fleet.vehicle.log.services'].create({
            'vehicle_id': cls.vehicle.id,
            'amount': 250.0,
            'service_type_id': cls.service_type.id,
            'date': date.today() - timedelta(days=15),
        })

        # Active contract
        cls.contract = cls.env['fleet.vehicle.log.contract'].create({
            'vehicle_id': cls.vehicle.id,
            'cost_generated': 500.0,
            'state': 'open',
            'expiration_date': date.today() + timedelta(days=30),
        })

    def test_get_tiles_data_as_manager(self):
        """get_tiles_data should return flag=1 and all dashboard keys for a fleet manager."""
        env_as_manager = self.env(user=self.manager_user)
        result = env_as_manager['fleet.vehicle'].get_tiles_data()

        self.assertIsInstance(result, dict)
        self.assertEqual(result['flag'], 1,
                         "Fleet manager should get flag=1 in tiles data")

        expected_keys = [
            'total_odometer', 'service_cost', 'recurring_cost',
            'all_vehicles', 'service_type', 'service_cost_list',
            'odometer_value_list', 'fleet_state', 'fleet_vehicle_list',
            'fleet_model_list', 'fleet_manufacture_list',
        ]
        for key in expected_keys:
            self.assertIn(key, result, f"Expected key '{key}' missing for manager view")

        self.assertGreaterEqual(result['total_odometer'], 1500.0)
        self.assertGreaterEqual(result['service_cost'], 250.0)
        self.assertGreaterEqual(result['recurring_cost'], 500.0)
        self.assertGreater(result['all_vehicles'], 0)

    def test_get_tiles_data_as_normal_user(self):
        """get_tiles_data should return flag=0 for a non-manager user."""
        env_as_user = self.env(user=self.normal_user)
        result = env_as_user['fleet.vehicle'].get_tiles_data()

        self.assertIsInstance(result, dict)
        self.assertEqual(result['flag'], 0,
                         "Normal user should get flag=0 in tiles data")

        expected_keys = [
            'total_odometer', 'service_cost', 'recurring_cost',
            'all_vehicles', 'service_type', 'service_cost_list',
            'odometer_value_list', 'fleet_state', 'model_list',
            'manufacture_list',
        ]
        for key in expected_keys:
            self.assertIn(key, result, f"Expected key '{key}' missing for normal user view")

    def test_get_graph_data_flag_1_services(self):
        """get_graph_data with flag=1 aggregates service amounts per month."""
        service_records = self.env['fleet.vehicle.log.services'].search(
            [('id', '=', self.service.id)]
        )
        result = self.env['fleet.vehicle'].get_graph_data(6, 1, service_records)

        self.assertIsInstance(result, list)
        # First element is always the header row
        self.assertEqual(result[0], ['Month', ''],
                         "Header row must be ['Month', '']")
        # Should have 6 monthly data points + 1 header = 7 items
        self.assertEqual(len(result), 7,
                         "Expected 7 items (header + 6 monthly entries)")

        # All data entries after header should be [str, numeric]
        for entry in result[1:]:
            self.assertEqual(len(entry), 2)
            self.assertIsInstance(entry[0], str)
            self.assertIsInstance(entry[1], (int, float))

    def test_get_graph_data_flag_0_odometer(self):
        """get_graph_data with flag=0 aggregates odometer values per month."""
        odometer_records = self.env['fleet.vehicle.odometer'].search(
            [('id', '=', self.odometer.id)]
        )
        result = self.env['fleet.vehicle'].get_graph_data(13, 0, odometer_records)

        self.assertIsInstance(result, list)
        self.assertEqual(result[0], ['Month', ''],
                         "Header row must be ['Month', '']")
        # 13 monthly data points + 1 header = 14 items
        self.assertEqual(len(result), 14,
                         "Expected 14 items (header + 13 monthly entries)")

        for entry in result[1:]:
            self.assertEqual(len(entry), 2)
            self.assertIsInstance(entry[0], str)
            self.assertIsInstance(entry[1], (int, float))
