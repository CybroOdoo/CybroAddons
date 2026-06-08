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
from odoo.fields import Date
from datetime import timedelta

@tagged('post_install', '-at_install')
class TestInspectionRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.user = cls.env['res.users'].create({
            'name': 'Test Inspector',
            'login': 'test_inspector',
            'email': 'inspector@test.com',
        })

        cls.vehicle_model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'}).id,
        })

        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.vehicle_model.id,
            'license_plate': 'TEST-123',
            'odometer': 10000,
        })

        cls.inspection_type = cls.env['vehicle.inspection'].create({
            'name': 'Monthly Safety Check',
            'inspection_period': 30,
            'reminder_notification_days': 5,
            'user_id': cls.user.id,
        })

    def test_inspection_request_flow(self):
        """Test the basic lifecycle of an inspection request."""
        # Create draft inspection request
        inspection = self.env['inspection.request'].create({
            'inspection_id': self.inspection_type.id,
            'vehicle_id': self.vehicle.id,
            'user_id': self.user.id,
            'inspection_date': Date.today(),
        })

        self.assertEqual(inspection.state, 'draft', "Inspection should default to 'draft' state")
        self.assertNotEqual(inspection.name, 'New', "New inspection should have a sequence assigned")
        
        # Confirm inspection
        inspection.action_confirm_inspection()
        self.assertEqual(inspection.state, 'new', "Inspection should be in 'new' state after confirmation")
        
        # Verify inspection.request.line is created
        inspection_line = self.env['inspection.request.line'].search([
            ('fleet_vehicle_id', '=', self.vehicle.id),
            ('inspection_id', '=', self.inspection_type.id)
        ])
        self.assertTrue(inspection_line, "An inspection request line should have been created")
        self.assertEqual(inspection_line.inspection_id.id, self.inspection_type.id)
        self.assertEqual(inspection_line.fleet_vehicle_id.id, self.vehicle.id)
        
        # Start inspection
        inspection.action_start_inspection()
        self.assertEqual(inspection.state, 'inspection_started', "Inspection should be in 'inspection_started' state")
        
        # Finish inspection
        inspection.action_finish_inspection()
        self.assertEqual(inspection.state, 'inspection_finished', "Inspection should be in 'inspection_finished' state")

    def test_create_service(self):
        """Test the creation of a service from an inspection request."""
        inspection = self.env['inspection.request'].create({
            'inspection_id': self.inspection_type.id,
            'vehicle_id': self.vehicle.id,
            'user_id': self.user.id,
        })
        
        action = inspection.action_create_service()
        
        self.assertTrue(inspection.service_reference, "Service reference should be set")
        self.assertEqual(action['res_model'], 'fleet.service.inspection')
        self.assertEqual(action['res_id'], inspection.service_reference)
        
        # Verify service details
        service = self.env['fleet.service.inspection'].browse(inspection.service_reference)
        self.assertEqual(service.inspection_reference, inspection.id)
        self.assertEqual(service.vehicle_id.id, self.vehicle.id)

    def test_cron_create_inspection_request(self):
        """Test automatic creation of inspection requests based on reminder dates."""
        # Create an inspection line that needs a reminder today
        next_inspection_date = Date.today() + timedelta(days=5) # reminder_notification_days is 5
        
        inspection_line = self.env['inspection.request.line'].create({
            'inspection_id': self.inspection_type.id,
            'fleet_vehicle_id': self.vehicle.id,
            'user_id': self.user.id,
            'inspection_period': self.inspection_type.inspection_period,
            'reminder_notification': self.inspection_type.reminder_notification_days,
            'next_inspection_date': next_inspection_date,
        })
        
        # Trigger the cron job method
        self.env['inspection.request'].action_create_inspection_request()
        
        # Check if a new inspection request was created for this line
        new_inspection = self.env['inspection.request'].search([
            ('inspection_line_reference', '=', inspection_line.id)
        ])
        
        self.assertTrue(new_inspection, "A new inspection request should have been created by the cron method")
        self.assertEqual(new_inspection.state, 'new', "The new request should be in 'new' state")
        self.assertEqual(new_inspection.vehicle_id.id, self.vehicle.id)
        self.assertEqual(new_inspection.inspection_date, next_inspection_date)
        
        # Check if the line's next_inspection_date was updated
        expected_next_date = next_inspection_date + timedelta(days=self.inspection_type.inspection_period)
        self.assertEqual(inspection_line.next_inspection_date, expected_next_date, "The next_inspection_date should be updated on the line")
