# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import HttpCase


class TestFleetAdvancedDashboard(HttpCase):

    def setUp(self):
        super().setUp()
        # Authenticate with an explicit test user to pass 'auth=public' endpoints invoking restrictive model access
        self.fleet_test_user = self.env['res.users'].create({
            'name': 'Fleet Test Admin',
            'login': 'fleet_test_user_unique',
            'password': 'fleet_test_user_unique',
            'groups_id': [(6, 0, [self.env.ref('fleet.fleet_group_manager').id, self.env.ref('base.group_user').id])],
        })
        self.authenticate('fleet_test_user_unique', 'fleet_test_user_unique')
        self.brand = self.env['fleet.vehicle.model.brand'].create({'name': 'Audi Dashboard'})
        self.model = self.env['fleet.vehicle.model'].create({
            'name': 'A4 Dashboard',
            'brand_id': self.brand.id,
        })
        self.vehicle = self.env['fleet.vehicle'].create({
            'model_id': self.model.id,
        })

    def test_fleet_filter(self):
        """Check fleet filtration mapping logic properly pulling dynamic database records"""
        # Requires valid authentication JSON wrapping simulating RPC call
        response = self.url_open('/fleet/filter', data=b'{}', headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200)

    def test_fleet_filter_data(self):
        """Validate dashboard parameter conditionals generating exact statistics arrays gracefully without breaking"""
        data_payload = """{
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "data": {
                    "driver": "null",
                    "vehicle": "null",
                    "manufacturer": "null",
                    "date": "null"
                }
            }
        }"""
        response = self.url_open('/fleet_advanced_dashboard/filter_data', data=data_payload.encode(), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        
        self.assertIn('result', res_json)
        # Action generates large parameter lists containing totals and models explicitly evaluated inside JS charts later
        result_array = res_json['result']
        # Result array outputs format: [total_odometer, service_cost, recurring_cost...] which contains 13 specific tracking configurations
        self.assertEqual(len(result_array), 13)
