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
from datetime import timedelta

from odoo import fields
from odoo.tests.common import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_collection')
class TestRouteConsolidatedBatch(TransactionCase):
    """Unit tests verifying batch consolidation across multiple route collection orders."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Route Recyclables',
            'code': 'RREC',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Route Test Partner',
        })
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Route Point 1',
            'partner_id': cls.partner.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Route PET Bottle',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
        })
        cls.route = cls.env['wm.route'].create({
            'date': fields.Date.today(),
            'state': 'running',
            'line_ids': [(0, 0, {'collection_point_id': cls.point.id})],
        })
        now = fields.Datetime.now()
        later = now + timedelta(hours=2)
        cls.order1 = cls.env['wm.collection.order'].create({
            'partner_id': cls.partner.id,
            'collection_point_id': cls.point.id,
            'route_id': cls.route.id,
            'scheduled_start': now,
            'scheduled_end': later,
            'state': 'in_progress',
            'order_line_ids': [(0, 0, {
                'category_id': cls.category.id,
                'product_id': cls.product.id,
                'estimated_weight': 100.0,
                'weight': 100.0,
            })],
        })
        cls.order2 = cls.env['wm.collection.order'].create({
            'partner_id': cls.partner.id,
            'collection_point_id': cls.point.id,
            'route_id': cls.route.id,
            'scheduled_start': now,
            'scheduled_end': later,
            'state': 'in_progress',
            'order_line_ids': [(0, 0, {
                'category_id': cls.category.id,
                'product_id': cls.product.id,
                'estimated_weight': 150.0,
                'weight': 150.0,
            })],
        })

    def test_route_completion_creates_consolidated_category_batch(self):
        """
        Completing all collection orders on a route automatically completes the
        route and aggregates orders into 1 consolidated Waste Batch per
        category.
        """
        # 1. Complete order 1; order 2 is still pending, so no route batch created yet
        self.order1.action_complete()
        batches_mid = self.env['waste.batch'].search([('route_id', '=', self.route.id)])
        self.assertEqual(len(batches_mid), 0, "Route-assigned orders must defer batch creation until route completion")

        # 2. Complete order 2; all orders on route are now complete, so route auto-completes & creates consolidated batch
        self.order2.action_complete()

        batches_after = self.env['waste.batch'].search([('route_id', '=', self.route.id)])
        self.assertEqual(len(batches_after), 1, "Exactly 1 consolidated batch must be created for the category on route completion")

        batch = batches_after[0]
        self.assertEqual(batch.category_id, self.category)
        self.assertEqual(batch.draft_quantity, 250.0, "Total batch weight must combine Order 1 (100kg) and Order 2 (150kg)")
        self.assertEqual(len(batch.collection_order_ids), 2)
        self.assertEqual(self.order1.waste_batch_count, 1, "Order 1 waste_batch_count must be 1 via route batch")
        self.assertEqual(self.order2.waste_batch_count, 1, "Order 2 waste_batch_count must be 1 via route batch")
        _logger.info('PASS: test_route_completion_creates_consolidated_category_batch')

    def test_standalone_orders_merge_into_open_draft_batch(self):
        """
        Standalone collection orders merge weight into an existing open (Draft)
        category batch if present.
        """
        now = fields.Datetime.now()
        later = now + timedelta(hours=2)
        s_order1 = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'scheduled_start': now,
            'scheduled_end': later,
            'state': 'in_progress',
            'order_line_ids': [(0, 0, {
                'category_id': self.category.id,
                'product_id': self.product.id,
                'weight': 80.0,
            })],
        })
        s_order1.action_complete()
        batches = self.env['waste.batch'].search([
            ('category_id', '=', self.category.id),
            ('route_id', '=', False),
            ('status', '=', 'draft'),
        ])
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0].draft_quantity, 80.0)

        s_order2 = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'scheduled_start': now,
            'scheduled_end': later,
            'state': 'in_progress',
            'order_line_ids': [(0, 0, {
                'category_id': self.category.id,
                'product_id': self.product.id,
                'weight': 120.0,
            })],
        })
        s_order2.action_complete()

        batches_after = self.env['waste.batch'].search([
            ('category_id', '=', self.category.id),
            ('route_id', '=', False),
            ('status', '=', 'draft'),
        ])
        self.assertEqual(len(batches_after), 1, "Standalone order 2 must merge into the existing open draft batch")
        self.assertEqual(batches_after[0].draft_quantity, 200.0, "Draft quantity must combine 80kg + 120kg = 200kg")
        self.assertIn(s_order1, batches_after[0].collection_order_ids)
        self.assertIn(s_order2, batches_after[0].collection_order_ids)
        _logger.info('PASS: test_standalone_orders_merge_into_open_draft_batch')

    def test_route_category_batches_idempotency_and_merging(self):
        """
        Calling action_create_route_category_batches repeatedly merges new
        completed orders per category without duplicating existing ones.
        """
        cat2 = self.env['wm.waste.category'].create({
            'name': 'Route Metals',
            'code': 'RMET',
        })
        prod2 = self.env['product.product'].create({
            'name': 'Route Metal Can',
            'is_waste_material': True,
            'wm_waste_category_id': cat2.id,
        })

        now = fields.Datetime.now()
        later = now + timedelta(hours=2)

        route2 = self.env['wm.route'].create({
            'date': fields.Date.today(),
            'state': 'running',
            'line_ids': [(0, 0, {'collection_point_id': self.point.id})],
        })

        o1 = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'route_id': route2.id,
            'scheduled_start': now,
            'scheduled_end': later,
            'state': 'in_progress',
            'order_line_ids': [
                (0, 0, {'category_id': self.category.id, 'product_id': self.product.id, 'weight': 50.0}),
                (0, 0, {'category_id': cat2.id, 'product_id': prod2.id, 'weight': 40.0}),
            ],
        })
        o1.action_complete()

        # First run creates batches for both categories
        batches1 = route2.action_create_route_category_batches()
        self.assertEqual(len(batches1), 2, "Should create 2 batches (1 per category)")

        # Second run with no new orders returns the same existing batches without creating duplicates
        batches2 = route2.action_create_route_category_batches()
        self.assertEqual(set(batches1.ids), set(batches2.ids), "Second call must be idempotent and return existing batches")

        # Add a new completed order to the route
        o2 = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'route_id': route2.id,
            'scheduled_start': now,
            'scheduled_end': later,
            'state': 'in_progress',
            'order_line_ids': [
                (0, 0, {'category_id': self.category.id, 'product_id': self.product.id, 'weight': 70.0}),
            ],
        })
        o2.action_complete()

        batches3 = route2.action_create_route_category_batches()
        self.assertEqual(len(batches3), 2, "Total batch count remains 2 (1 per category)")
        rec_batch = batches3.filtered(lambda b: b.category_id == self.category)
        self.assertEqual(rec_batch.draft_quantity, 120.0, "Draft quantity for Recyclables category merged 50kg + 70kg = 120kg")
        self.assertIn(o1, rec_batch.collection_order_ids)
        self.assertIn(o2, rec_batch.collection_order_ids)
        self.assertEqual(o1.waste_batch_count, 2, "Order 1 linked to both category batches")
        self.assertEqual(o2.waste_batch_count, 1, "Order 2 linked to recyclables category batch")
        _logger.info('PASS: test_route_category_batches_idempotency_and_merging')
