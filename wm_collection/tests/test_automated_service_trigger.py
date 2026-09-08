# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'wm_fleet')
class TestAutomatedServiceTrigger(TransactionCase):
    """Unit tests verifying recurring schedule triggers for collection order creation."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Truck Brand'})
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'Compactor Truck',
            'brand_id': cls.brand.id
        })
        cls.main_truck = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'WM-FAIL-01',
        })
        cls.standby_truck = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'WM-STANDBY-02',
        })
        cls.survey = cls.env['survey.survey'].create({
            'title': 'Pre-Trip Safety Inspection',
            'scoring_type': 'scoring_with_answers',
        })
        cls.question = cls.env['survey.question'].create({
            'survey_id': cls.survey.id,
            'title': 'Brake System Functionality',
            'question_type': 'simple_choice',
        })
        cls.driver_partner = cls.env['res.partner'].create({'name': 'Driver John'})
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Pickup Point A',
            'partner_id': cls.driver_partner.id,
        })
        cls.route = cls.env['wm.route'].create({
            'name': 'Morning Route 101',
            'vehicle_id': cls.main_truck.id,
            'driver_id': cls.driver_partner.id,
            'state': 'to_start',
        })

    def test_inspection_failure_triggers_service_log_and_reassigns_standby_vehicle(self):
        """
        Test that completing a failed Pre-Trip inspection sets vehicle to
        maintenance, creates service log, and reassigns route to standby
        vehicle.
        """
        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'vehicle_id': self.main_truck.id,
            'route_id': self.route.id,
            'checklist_type': 'pre_trip',
            'state': 'in_progress',
        })

        # Log a failed line
        self.env['survey.user_input.line'].create({
            'user_input_id': user_input.id,
            'question_id': self.question.id,
            'answer_type': 'char_box',
            'value_char_box': 'Fail',
            'answer_score': 0.0,
            'skipped': False,
        })

        # Mark inspection as done
        user_input._mark_done()

        # 1. Verify vehicle status changed to maintenance
        if 'state' in self.main_truck._fields:
            self.assertEqual(self.main_truck.state, 'maintenance', "Failed inspection should set vehicle state to 'maintenance'")
        elif self.main_truck.state_id:
            self.assertTrue(any(w in (self.main_truck.state_id.name or '').lower() for w in ('maintenance', 'downgrade', 'inactive', 'repair')))

        # 2. Verify service log was created
        services = self.env['fleet.vehicle.log.services'].search([('vehicle_id', '=', self.main_truck.id)])
        self.assertTrue(services, "A fleet service request log should be automatically created")
        self.assertIn("AUTOMATED INSPECTION FAILURE TRIGGER", services[0].description)

        # 3. Verify route was reassigned to standby truck
        self.assertEqual(self.route.vehicle_id.id, self.standby_truck.id, "Pending route should be reassigned to standby vehicle")
