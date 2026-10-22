# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for Purchase Line Views module."""

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPurchaseLineViews(TransactionCase):
    """Test cases for purchase line views, actions, and models."""

    @classmethod
    def setUpClass(cls):
        """Set up test data: partner, product, and purchase orders."""
        super().setUpClass()
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test Supplier',
            'supplier_rank': 1,
        })
        sample_img = (
            'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
        )
        cls.product = cls.env['product.product'].create({
            'name': 'Procurement Test Product',
            'standard_price': 50.0,
            'list_price': 100.0,
            'image_1920': sample_img,
        })
        cls.rfq = cls.env['purchase.order'].create({
            'partner_id': cls.vendor.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'name': 'Procurement Test Product',
                    'product_qty': 5.0,
                    'price_unit': 50.0,
                }),
            ],
        })
        cls.confirmed_po = cls.env['purchase.order'].create({
            'partner_id': cls.vendor.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'name': 'Procurement Test Product',
                    'product_qty': 10.0,
                    'price_unit': 50.0,
                }),
            ],
        })
        cls.confirmed_po.button_confirm()

    def test_actions_configuration(self):
        """Verify actions contain calendar mode, correct domains and contexts.
        """
        action_po = self.env.ref(
            'purchase_line_views.action_purchase_order_line_view'
        )
        self.assertEqual(action_po.res_model, 'purchase.order.line')
        self.assertIn('calendar', action_po.view_mode)
        self.assertEqual(
            action_po.domain,
            "[('state', 'in', ['purchase', 'done'])]"
        )
        self.assertIn('is_purchase_line_view', action_po.context)

        action_rfq = self.env.ref(
            'purchase_line_views.action_rfq_order_line_view'
        )
        self.assertEqual(action_rfq.res_model, 'purchase.order.line')
        self.assertIn('calendar', action_rfq.view_mode)
        self.assertEqual(
            action_rfq.domain,
            "[('state', 'in', ['draft', 'sent', 'to approve'])]"
        )
        self.assertIn('is_rfq_line', action_rfq.context)

    def test_views_existence(self):
        """Verify all dedicated view records exist and are linked."""
        view_refs = [
            'purchase_line_views.purchase_order_line_view_search',
            'purchase_line_views.purchase_order_line_tree_view',
            'purchase_line_views.purchase_order_line_form_view',
            'purchase_line_views.purchase_order_line_kanban_view',
            'purchase_line_views.purchase_order_line_view_pivot',
            'purchase_line_views.purchase_order_line_graph_view',
            'purchase_line_views.purchase_order_line_view_calendar',
            'purchase_line_views.rfq_line_form_view',
            'purchase_line_views.rfq_line_tree_view',
            'purchase_line_views.rfq_line_kanban_view',
            'purchase_line_views.rfq_line_view_pivot',
            'purchase_line_views.rfq_line_graph_view',
            'purchase_line_views.rfq_line_view_calendar',
        ]
        for ref_id in view_refs:
            view = self.env.ref(ref_id)
            self.assertTrue(view, f"View {ref_id} should exist")
            self.assertEqual(view.model, 'purchase.order.line')

    def test_product_image_field(self):
        """Test product_image related field on purchase.order.line."""
        line = self.rfq.order_line[0]
        self.assertTrue(line.product_image)
        self.assertEqual(line.product_image, self.product.image_1920)

    def test_compute_display_name(self):
        """Test display name computation with and without context guard."""
        line = self.rfq.order_line[0]
        # Standard context should use base display name behavior
        line_standard = line.with_context(is_purchase_line_view=False)
        line_standard._compute_display_name()

        # Context-guarded purchase line view display name
        line_custom = line.with_context(is_purchase_line_view=True)
        line_custom._compute_display_name()
        self.assertEqual(line_custom.display_name,
                         self.product.display_name)

    def test_onchange_order_id_warning(self):
        """Verify onchange returns a warning instead of raising UserError."""
        line = self.rfq.order_line[0]
        # In RFQ context with confirmed order
        line_with_context = line.with_context(is_rfq_line=True)
        line_with_context.order_id = self.confirmed_po
        res = line_with_context._onchange_order_id()
        self.assertIsInstance(res, dict)
        self.assertIn('warning', res)
        self.assertIn('title', res['warning'])
        self.assertIn('message', res['warning'])

        # In RFQ context with draft RFQ order: no warning
        line_with_context.order_id = self.rfq
        res_draft = line_with_context._onchange_order_id()
        self.assertFalse(res_draft)

        # In standard context without is_rfq_line: no warning even if confirmed
        line_no_ctx = line.with_context(is_rfq_line=False)
        line_no_ctx.order_id = self.confirmed_po
        res_standard = line_no_ctx._onchange_order_id()
        self.assertFalse(res_standard)

    def test_adding_line_to_confirmed_po_not_blocked(self):
        """Verify adding lines to confirmed purchase order is not blocked."""
        self.assertEqual(self.confirmed_po.state, 'purchase')
        new_line = self.env['purchase.order.line'].create({
            'order_id': self.confirmed_po.id,
            'product_id': self.product.id,
            'name': 'Additional Line',
            'product_qty': 2.0,
            'price_unit': 45.0,
        })
        self.assertTrue(new_line.id)
        self.assertEqual(new_line.order_id.id, self.confirmed_po.id)
