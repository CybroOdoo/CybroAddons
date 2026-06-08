# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestFleetVehicle(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        cls.vehicle_model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Model 2',
            'brand_id': cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand 2'}).id,
        })

        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.vehicle_model.id,
            'license_plate': 'TEST-456',
            'odometer': 5000,
        })
        
        cls.inspection_type = cls.env['vehicle.inspection'].create({
            'name': 'Weekly Safety Check',
            'inspection_period': 7,
            'reminder_notification_days': 2,
        })

    def test_fleet_vehicle_methods(self):
        """Test methods in fleet.vehicle model"""
        inspection = self.env['inspection.request'].create({
            'inspection_id': self.inspection_type.id,
            'vehicle_id': self.vehicle.id,
        })
        
        # Test _compute_inspection_count
        self.vehicle._compute_inspection_count()
        self.assertEqual(self.vehicle.inspection_count, 1)
        
        # Test get_inspection_requests smart button
        action = self.vehicle.get_inspection_requests()
        self.assertEqual(action['res_model'], 'inspection.request')
