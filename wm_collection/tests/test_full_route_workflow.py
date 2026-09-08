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
import logging
from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_collection', 'full_workflow')
class TestFullRouteWorkflow(TransactionCase):
    """Unit tests verifying complete route planning, dispatch, execution, and completion."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.category_paper = cls.env['wm.waste.category'].create({
            'name': 'Recyclable Paper Stream',
            'code': 'RPAPER',
            'price': 0.75,
            'auto_create_batches_on_collection': True,
        })
        cls.product_paper = cls.env['product.product'].create({
            'name': 'Mixed Shredded Paper',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category_paper.id,
            'list_price': 0.85,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Commercial Waste Generator Partner'})

        # 1. Create Partner Contract
        today = date.today()
        cls.contract = cls.env['wm.partner.contract'].create({
            'name': 'CNT-WORKFLOW-001',
            'partner_id': cls.partner.id,
            'from_date': today - timedelta(days=30),
            'to_date': today + timedelta(days=335),
            'billing_mode': 'monthly_run',
            'contract_line_ids': [(0, 0, {
                'waste_category_id': cls.category_paper.id,
                'weight': 100.0,
                'price_per_kg': 0.75,
            })],
        })

        # 2. Create Collection Point and Vehicle/Driver
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Generator HQ Waste Bay',
            'partner_id': cls.partner.id,
        })
        cls.route = cls.env['wm.route'].create({'name': 'Downtown Commercial Route A1'})

        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Volvo Commercial'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'FE Electric Waste Truck', 'brand_id': brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id,
            'driver_id': cls.partner.id,
            'license_plate': 'WF-TEST-99',
        })

        cls.route.write({
            'vehicle_id': cls.vehicle.id,
            'driver_id': cls.partner.id,
            'line_ids': [(0, 0, {'collection_point_id': cls.point.id, 'sequence': 10})],
        })

        # 3. Create Pre-trip Inspection Record
        cls.env['wm.vehicle.maintenance.checklist'].create({
            'name': 'PRE-TRIP-WF-TEST',
            'vehicle_id': cls.vehicle.id,
            'route_id': cls.route.id,
            'checklist_type': 'pre_trip',
            'state': 'checked',
        })

    def test_complete_route_blocked_with_undefined_weight(self):
        """
        Test that completing a collection order or route with undefined (0)
        weight is blocked with ValidationError.
        """
        order = self.env['wm.collection.order'].create({
            'name': 'ORD-WF-ZERO-01',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'route_id': self.route.id,
            'vehicle_id': self.vehicle.id,
            'driver_id': self.partner.id,
            'company_id': self.env.company.id,
            'scheduled_start': fields.Datetime.now(),
            'order_line_ids': [(0, 0, {
                'category_id': self.category_paper.id,
                'product_id': self.product_paper.id,
                'estimated_weight': 100.0,
                'weight': 0.0,  # Undefined weight
            })],
        })

        # Dispatch Route
        self.route.action_dispatch_route()
        self.assertEqual(self.route.state, 'dispatched')
        self.assertEqual(order.state, 'dispatched')

        # 1. Attempting to complete the collection order with 0 weight must fail
        with self.assertRaises(ValidationError) as cm:
            order.action_complete()
        self.assertIn("zero or unrecorded weights", str(cm.exception))

        # 2. Attempting to complete the route while order is pending must fail
        with self.assertRaises(ValidationError) as cm_route:
            self.route.action_complete_route()
        self.assertIn("collection order(s) are still pending", str(cm_route.exception))

    def test_full_workflow_end_to_end_success(self):
        """
        Test full workflow from dispatch to recorded weights, order completion,
        route completion, waste batching, and monthly billing.
        """
        order = self.env['wm.collection.order'].create({
            'name': 'ORD-WF-SUCCESS-01',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'route_id': self.route.id,
            'vehicle_id': self.vehicle.id,
            'driver_id': self.partner.id,
            'company_id': self.env.company.id,
            'scheduled_start': fields.Datetime.now(),
            'order_line_ids': [(0, 0, {
                'category_id': self.category_paper.id,
                'product_id': self.product_paper.id,
                'estimated_weight': 100.0,
                'weight': 0.0,
            })],
        })

        # Step A: Dispatch Route
        self.route.action_dispatch_route()
        self.assertEqual(self.route.state, 'dispatched')

        # Step B: Record valid confirmed weight
        order.order_line_ids[0].write({'weight': 125.0})

        # Step C: Complete Collection Order
        order.action_complete()
        self.assertEqual(order.state, 'completed')

        # Step D: Complete Route
        self.route.action_complete_route()
        self.assertEqual(self.route.state, 'completed')

        # Step E: Verify Waste Batch creation
        batches = self.env['waste.batch'].search([('category_id', '=', self.category_paper.id)])
        self.assertTrue(batches, "Waste batch must be generated upon route completion")
        self.assertIn(order.id, batches[0].collection_order_ids.ids)
        self.assertEqual(batches[0].intake_weight, 125.0)

        # Step F: Verify Monthly Billing Run
        today = date.today()
        billing_run = self.env['wm.monthly.billing.run'].create({
            'name': 'RUN-FULL-WF-TEST',
            'partner_ids': [(6, 0, [self.partner.id])],
            'period_start': today - timedelta(days=5),
            'period_end': today + timedelta(days=5),
        })
        billing_run.action_run_billing()
        self.assertEqual(billing_run.state, 'completed')

        # Verify generated Invoice
        invoice = self.env['account.move'].search([('partner_id', '=', self.partner.id)])
        self.assertTrue(invoice, "Invoice must be generated for completed collection order in billing run")
        self.assertEqual(order.billing_run_line_id.billing_run_id.id, billing_run.id)
