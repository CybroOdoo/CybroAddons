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
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestRouteInspectionPass(TransactionCase):
    """Unit tests verifying vehicle pre-trip inspection enforcement before route dispatch."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Inspection Customer'})
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Inspection Point',
            'partner_id': cls.partner.id,
        })
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'InspPass Brand'})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.env.ref('fleet.model_a3').id if cls.env.ref('fleet.model_a3', raise_if_not_found=False) else cls.env['fleet.vehicle.model'].create({'name': 'Truck InspPass', 'brand_id': brand.id}).id,
            'license_plate': 'INSP-101',
        })
        cls.survey = cls.env['survey.survey'].create({
            'title': 'Pre-Trip Checklist Test',
            'scoring_type': 'no_scoring',
        })

    def test_failed_inspection_blocks_dispatch(self):
        """
        Test that a failed survey response blocks route dispatch.
        """
        route = self.env['wm.route'].create({
            'name': 'Route Fail Test',
            'vehicle_id': self.vehicle.id,
            'driver_id': self.partner.id,
        })
        self.env['wm.route.line'].create({
            'route_id': route.id,
            'collection_point_id': self.point.id,
        })

        # Create a failed user input response
        self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'route_id': route.id,
            'checklist_type': 'pre_trip',
            'state': 'done',
            'scoring_success': False,
        })

        route.invalidate_recordset(['is_inspected', 'is_ready_to_dispatch'])
        self.assertFalse(route.is_inspected)
        self.assertFalse(route.is_ready_to_dispatch)

        with self.assertRaises(ValidationError):
            route.action_dispatch_route()

    def test_passed_inspection_allows_dispatch(self):
        """
        Test that a passed survey response allows route dispatch.
        """
        route = self.env['wm.route'].create({
            'name': 'Route Pass Test',
            'vehicle_id': self.vehicle.id,
            'driver_id': self.partner.id,
        })
        self.env['wm.route.line'].create({
            'route_id': route.id,
            'collection_point_id': self.point.id,
        })

        # Create a passed user input response
        self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'route_id': route.id,
            'checklist_type': 'pre_trip',
            'state': 'done',
            'scoring_success': True,
        })

        route.invalidate_recordset(['is_inspected', 'is_ready_to_dispatch'])
        self.assertTrue(route.is_inspected)

        route.action_dispatch_route()
        self.assertEqual(route.state, 'dispatched')

    def test_subsequent_passed_inspection_allows_dispatch_after_failed(self):
        """
        Test that when an initial inspection failed, but a subsequent pre-trip
        inspection is performed and passes, the route is unblocked and can be dispatched.
        """
        route = self.env['wm.route'].create({
            'name': 'Route Fail Then Pass Test',
            'vehicle_id': self.vehicle.id,
            'driver_id': self.partner.id,
        })
        self.env['wm.route.line'].create({
            'route_id': route.id,
            'collection_point_id': self.point.id,
        })

        # 1. Initial failed inspection
        self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'route_id': route.id,
            'checklist_type': 'pre_trip',
            'state': 'done',
            'scoring_success': False,
        })

        route.invalidate_recordset(['is_inspected', 'is_ready_to_dispatch'])
        self.assertFalse(route.is_inspected)
        with self.assertRaises(ValidationError):
            route.action_dispatch_route()

        # 2. Subsequent passed inspection
        self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'route_id': route.id,
            'checklist_type': 'pre_trip',
            'state': 'done',
            'scoring_success': True,
        })

        route.invalidate_recordset(['is_inspected', 'is_ready_to_dispatch'])
        self.assertTrue(route.is_inspected)
        self.assertTrue(route.is_ready_to_dispatch)

        # 3. Route can now be dispatched
        route.action_dispatch_route()
        self.assertEqual(route.state, 'dispatched')

    def test_passed_inspection_restores_vehicle_maintenance_state(self):
        """
        Test that completing a passing inspection restores vehicle state to available.
        """
        self.vehicle.write({'state': 'maintenance'})
        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'vehicle_id': self.vehicle.id,
            'checklist_type': 'pre_trip',
            'state': 'in_progress',
        })
        user_input._mark_done()
        self.assertEqual(self.vehicle.state, 'available', "Passing inspection should restore vehicle state to 'available'")

    def test_toggle_is_inspected_controls_dispatch_and_reinspection(self):
        """
        Test that is_inspected boolean can be toggled to re-enable inspection requirement or permit dispatch.
        """
        route = self.env['wm.route'].create({
            'name': 'Route Toggle Test',
            'vehicle_id': self.vehicle.id,
            'driver_id': self.partner.id,
        })
        self.env['wm.route.line'].create({
            'route_id': route.id,
            'collection_point_id': self.point.id,
        })

        # By default without inspection, is_inspected is False
        self.assertFalse(route.is_inspected)
        with self.assertRaises(ValidationError):
            route.action_dispatch_route()

        # User toggles is_inspected to True
        route.write({'is_inspected': True})
        self.assertTrue(route.is_inspected)
        self.assertTrue(route.is_ready_to_dispatch)

        # User toggles is_inspected back to False to require re-inspection
        route.write({'is_inspected': False})
        self.assertFalse(route.is_inspected)
        self.assertFalse(route.is_ready_to_dispatch)
        with self.assertRaises(ValidationError):
            route.action_dispatch_route()
