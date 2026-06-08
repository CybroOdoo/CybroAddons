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
class TestFleetServiceInspection(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        cls.vehicle_model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Model 3',
            'brand_id': cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand 3'}).id,
        })

        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.vehicle_model.id,
            'license_plate': 'TEST-789',
            'odometer': 5500,
        })
        
        cls.inspection_type = cls.env['vehicle.inspection'].create({
            'name': 'Weekly Safety Check',
            'inspection_period': 7,
            'reminder_notification_days': 2,
        })

    def test_fleet_service_inspection_wizard(self):
        """Test wizard action_create_service"""
        service_type = self.env['fleet.service.type'].create({
            'name': 'Brake Check',
            'category': 'service',
        })
        
        inspection = self.env['inspection.request'].create({
            'inspection_id': self.inspection_type.id,
            'vehicle_id': self.vehicle.id,
        })
        
        wizard = self.env['fleet.service.inspection'].create({
            'inspection_reference': inspection.id,
            'vehicle_id': self.vehicle.id,
            'service_type_id': service_type.id,
            'odometer': 5500,
            'odometer_unit': 'kilometers',
        })
        
        wizard._onchange_service_category()
        self.assertEqual(wizard.service_category, 'service')
        
        wizard.action_create_service()
        
        # Verify fleet.vehicle.log.services is created
        service = self.env['fleet.vehicle.log.services'].search([
            ('inspection_reference', '=', wizard.id)
        ])
        self.assertTrue(service)
        
        # Verify vehicle.service.log is created
        service_log = self.env['vehicle.service.log'].search([
            ('service_reference', '=', wizard.id)
        ])
        self.assertTrue(service_log)
