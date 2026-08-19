# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class TestEmployeeFleet(TransactionCase):

    def setUp(self):
        super(TestEmployeeFleet, self).setUp()
        
        # Create a test employee
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
            'work_email': 'test@example.com',
        })
        
        # Create a test vehicle model and vehicle
        self.vehicle_model = self.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': self.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'}).id,
        })
        self.vehicle = self.env['fleet.vehicle'].create({
            'model_id': self.vehicle_model.id,
            'license_plate': 'TEST-001',
            'check_availability': True,
        })
        
        self.date_now = datetime.now()
        self.date_tomorrow = self.date_now + timedelta(days=1)
        self.date_next_week = self.date_now + timedelta(days=7)

    def test_01_create_request(self):
        """Test sequence generation and default values on creation."""
        request = self.env['employee.fleet'].create({
            'employee_id': self.employee.id,
            'fleet_id': self.vehicle.id,
            'date_from': self.date_now,
            'date_to': self.date_tomorrow,
            'purpose': 'Business Trip',
        })
        self.assertTrue(request.name)
        self.assertEqual(request.state, 'draft')

    def test_02_onchange_date_validation(self):
        """Test date validation."""
        request = self.env['employee.fleet'].new({
            'employee_id': self.employee.id,
            'fleet_id': self.vehicle.id,
            'date_from': self.date_tomorrow,
            'date_to': self.date_now,
            'purpose': 'Invalid Dates',
        })
        with self.assertRaises(ValidationError):
            request.onchange_date_to()

    def test_03_action_send_and_approve(self):
        """Test successful request, reservation creation, and approval."""
        request = self.env['employee.fleet'].create({
            'employee_id': self.employee.id,
            'fleet_id': self.vehicle.id,
            'date_from': self.date_now,
            'date_to': self.date_tomorrow,
            'purpose': 'Business Trip',
        })
        
        # Send request
        request.action_send()
        self.assertEqual(request.state, 'waiting')
        self.assertTrue(request.reserved_fleet_id)
        
        # Approve request
        request.action_approve()
        self.assertEqual(request.state, 'confirm')
        self.assertFalse(self.vehicle.check_availability)

    def test_04_overlapping_request(self):
        """Test overlap prevention."""
        request1 = self.env['employee.fleet'].create({
            'employee_id': self.employee.id,
            'fleet_id': self.vehicle.id,
            'date_from': self.date_now,
            'date_to': self.date_next_week,
            'purpose': 'Trip 1',
        })
        request1.action_send()
        
        request2 = self.env['employee.fleet'].create({
            'employee_id': self.employee.id,
            'fleet_id': self.vehicle.id,
            'date_from': self.date_tomorrow,
            'date_to': self.date_next_week,
            'purpose': 'Trip 2',
        })
        
        # Test onchange overlap check
        request2_new = self.env['employee.fleet'].new({
            'employee_id': self.employee.id,
            'fleet_id': self.vehicle.id,
            'date_from': self.date_tomorrow,
            'date_to': self.date_next_week,
            'purpose': 'Trip 2',
        })
        with self.assertRaises(ValidationError):
            request2_new.onchange_fleet_availability()
            
        # Test action_send overlap check
        with self.assertRaises(ValidationError):
            request2.action_send()

    def test_05_action_reject(self):
        """Test rejection unlinks reservation."""
        request = self.env['employee.fleet'].create({
            'employee_id': self.employee.id,
            'fleet_id': self.vehicle.id,
            'date_from': self.date_now,
            'date_to': self.date_tomorrow,
            'purpose': 'To be rejected',
        })
        request.action_send()
        self.assertTrue(request.reserved_fleet_id)
        
        request.action_reject()
        self.assertEqual(request.state, 'reject')
        self.assertFalse(request.reserved_fleet_id.exists())
        self.assertTrue(self.vehicle.check_availability)
        
    def test_06_action_cancel(self):
        """Test cancel unlinks reservation."""
        request = self.env['employee.fleet'].create({
            'employee_id': self.employee.id,
            'fleet_id': self.vehicle.id,
            'date_from': self.date_now,
            'date_to': self.date_tomorrow,
            'purpose': 'To be cancelled',
        })
        request.action_send()
        request.action_cancel()
        self.assertEqual(request.state, 'cancel')
        self.assertFalse(request.reserved_fleet_id.exists())
        
    def test_07_action_return(self):
        """Test return logic."""
        request = self.env['employee.fleet'].create({
            'employee_id': self.employee.id,
            'fleet_id': self.vehicle.id,
            'date_from': self.date_now,
            'date_to': self.date_tomorrow,
            'purpose': 'To be returned',
        })
        request.action_send()
        request.action_approve()
        
        request.action_return()
        self.assertEqual(request.state, 'return')
        self.assertTrue(request.returned_date)
        self.assertFalse(request.reserved_fleet_id.exists())
        self.assertTrue(self.vehicle.check_availability)
