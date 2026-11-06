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

from datetime import date
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestFleetVehicle(TransactionCase):

    def setUp(self):
        super().setUp()
        self.brand = self.env['fleet.vehicle.model.brand'].create({'name': 'Audi'})
        self.model = self.env['fleet.vehicle.model'].create({
            'name': 'A4',
            'brand_id': self.brand.id,
        })
        self.vehicle = self.env['fleet.vehicle'].create({
            'model_id': self.model.id,
        })
        
        # We create some sample service types/records
        self.service_type = self.env['fleet.service.type'].create({
            'name': 'Oil Change',
            'category': 'service',
        })
        self.service = self.env['fleet.vehicle.log.services'].create({
            'vehicle_id': self.vehicle.id,
            'service_type_id': self.service_type.id,
            'amount': 250.0,
            'date': date.today(),
        })
        
        # Sample odometer
        self.odometer = self.env['fleet.vehicle.odometer'].create({
            'vehicle_id': self.vehicle.id,
            'value': 15000,
            'date': date.today(),
        })

    def test_get_tiles_data(self):
        """Test the tiles dictionary maps the database parameters accurately"""
        # Testing in Admin/Manager logic
        data = self.env['fleet.vehicle'].get_tiles_data(model_id='null')
        
        self.assertIn('service_cost', data)
        # Verify 250 logic captured
        self.assertTrue(data['service_cost'] >= 250.0)
        
        # Verify lists mapped
        self.assertIn('fleet_vehicle_list', data)
        self.assertIn(self.vehicle.id, data['fleet_vehicle_list'])
        
        self.assertIn('fleet_model_list', data)
        self.assertIn(self.model.id, data['fleet_model_list'])
        
        self.assertIn('fleet_manufacture_list', data)
        self.assertIn(self.brand.id, data['fleet_manufacture_list'])

    def test_get_tiles_data_non_manager(self):
        """Test the tiles dictionary for non-manager user"""
        self.vehicle.manager_id = self.env.uid
        with patch.object(type(self.env.user), 'has_group', return_value=False):
            data = self.env['fleet.vehicle'].get_tiles_data(model_id='null')
            self.assertEqual(data['flag'], 0)
            self.assertIn('all_vehicles', data)
            self.assertEqual(data['all_vehicles'], 1)
            self.assertTrue(all('id' in s for s in data['fleet_state']))

    def test_get_graph_data(self):
        """Test chart generation for 6 months tracking total data structures"""
        # Passing mock list for parameter checking behavior
        res_service = self.env['fleet.vehicle'].get_graph_data(6, 1, self.env['fleet.vehicle.log.services'].search([]))
        
        # It should generate a list with element [0] == ['Month', ''] and 6 monthly arrays appended
        self.assertEqual(len(res_service), 7)
        self.assertEqual(res_service[0][0], 'Month')
        
        # Now pass mock list checking odometer arrays (6 months tracking)
        res_odometer = self.env['fleet.vehicle'].get_graph_data(6, 0, self.env['fleet.vehicle.odometer'].search([]))
        self.assertEqual(len(res_odometer), 7)
        self.assertEqual(res_odometer[0][0], 'Month')
