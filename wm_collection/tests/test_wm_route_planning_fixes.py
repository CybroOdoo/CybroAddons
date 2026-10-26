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
import logging

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestWmRoutePlanningFixes(TransactionCase):
    """Unit tests verifying route stop sequencing and vehicle capacity calculations."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Route Partner'})
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Test Collection Point 1',
            'partner_id': cls.partner.id,
            'latitude': 37.7749,
            'longitude': -122.4194,
        })
        cls.point2 = cls.env['wm.collection.point'].create({
            'name': 'Test Collection Point 2',
            'partner_id': cls.partner.id,
            'latitude': 37.7833,
            'longitude': -122.4167,
        })
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Truck Brand'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'Test Heavy Hauler', 'brand_id': brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'license_plate': 'WM-ROUTE-TEST-99',
            'model_id': model.id,
        })
        cls.route = cls.env['wm.route'].create({
            'name': 'Test Collection Route',
            'date': fields.Date.today(),
            'vehicle_id': cls.vehicle.id,
            'state': 'to_start',
        })
        cls.env['wm.vehicle.maintenance.checklist'].create({
            'name': 'PRE-TRIP-ROUTE-TEST',
            'vehicle_id': cls.vehicle.id,
            'checklist_type': 'pre_trip',
            'state': 'checked',
        })

    def test_add_collection_point_links_existing_draft_order(self):
        """
        Bug 1 Fix: Adding a point to a route links an existing draft order
        instead of creating a duplicate order.
        """
        existing_order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'scheduled_start': fields.Datetime.now(),
            'state': 'draft',
        })
        self.assertFalse(existing_order.route_id, "Order should initially have no route.")

        # Add collection point to route
        self.route.action_add_collection_point(self.point.id)

        # Verify existing order was linked and no duplicate order was created
        orders = self.env['wm.collection.order'].search([
            ('collection_point_id', '=', self.point.id)
        ])
        self.assertEqual(len(orders), 1, "Only one collection order must exist for the point.")
        self.assertEqual(orders.id, existing_order.id, "Existing order must be linked to the route.")
        self.assertEqual(existing_order.route_id.id, self.route.id, "Order route_id must match the route.")
        _logger.info("PASS: test_add_collection_point_links_existing_draft_order")

    def test_route_state_sync_dispatches_and_completes_orders(self):
        """
        Route dispatch and start synchronize to linked orders, while completion
        requires all orders to be completed/missed.
        """
        self.route.action_add_collection_point(self.point.id)
        order = self.env['wm.collection.order'].search([
            ('route_id', '=', self.route.id),
            ('collection_point_id', '=', self.point.id)
        ], limit=1)
        self.assertEqual(order.state, 'draft', "Order must start in draft state.")

        # Dispatch route
        self.route.action_dispatch_route()
        self.assertEqual(self.route.state, 'dispatched')
        order.invalidate_recordset(['state'])
        self.assertEqual(order.state, 'dispatched', "Linked order must transition to dispatched.")

        # Start route
        self.route.action_start_route()
        self.assertEqual(self.route.state, 'running')
        order.invalidate_recordset(['state'])
        self.assertEqual(
            order.state, 'dispatched',
            "Linked order must remain 'dispatched' after route start; "
            "it moves to 'in_progress' only when the driver taps 'Started' on the stop.",
        )

        # Trying to complete route with a still-dispatched order raises ValidationError
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.route.action_complete_route()

        # Mark order as completed -> route automatically completes when all orders are finished
        order.with_context(programmatic_state_change=True).write({'state': 'completed'})
        self.route.invalidate_recordset(['state'])
        self.assertEqual(self.route.state, 'completed', "Route must automatically complete when all orders are finished.")
        _logger.info("PASS: test_route_state_sync_dispatches_and_completes_orders")

    def test_tsp_sequence_lock_on_active_route(self):
        """
        Bug 3 Fix: Re-optimizing TSP sequence is blocked when route is
        dispatched/running.
        """
        self.route.action_add_collection_point(self.point.id)
        self.route.action_add_collection_point(self.point2.id)

        self.route.action_dispatch_route()
        self.assertEqual(self.route.state, 'dispatched')

        with self.assertRaises(UserError):
            self.route.action_optimize_route()
        _logger.info("PASS: test_tsp_sequence_lock_on_active_route")

    def test_dispatch_and_start_without_vehicle_raises_validation_error(self):
        """
        Verify that attempting to dispatch or start a route without an assigned vehicle
        raises a ValidationError.
        """
        from odoo.exceptions import ValidationError
        unassigned_route = self.env['wm.route'].create({
            'name': 'Unassigned Vehicle Route',
            'date': fields.Date.today(),
            'vehicle_id': False,
            'state': 'to_start',
        })
        self.env['wm.route.line'].create({
            'route_id': unassigned_route.id,
            'collection_point_id': self.point.id,
            'sequence': 10,
        })
        with self.assertRaises(ValidationError):
            unassigned_route.action_dispatch_route()

        unassigned_route.state = 'dispatched'
        with self.assertRaises(ValidationError):
            unassigned_route.action_start_route()
        _logger.info("PASS: test_dispatch_and_start_without_vehicle_raises_validation_error")

    def test_change_vehicle_prohibited_when_inspected(self):
        """
        Verify that changing the vehicle on an inspected route raises UserError
        once the route is dispatched. A to_start route only covered by the
        vehicle's pre-trip checklist may still switch vehicles.
        """
        other_vehicle = self.env['fleet.vehicle'].create({
            'license_plate': 'WM-OTHER-TRUCK-01',
            'model_id': self.vehicle.model_id.id,
        })
        self.assertTrue(self.route.is_inspected, "Route should be inspected in setup.")
        self.route.with_context(programmatic_state_change=True).write({'state': 'dispatched'})
        with self.assertRaises(UserError):
            self.route.write({'vehicle_id': other_vehicle.id})
        _logger.info("PASS: test_change_vehicle_prohibited_when_inspected")
