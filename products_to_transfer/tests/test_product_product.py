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
"""Unit tests for the product.product model extensions."""

from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestProductProduct(TransactionCase):
    """Test cases for product.product action methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Consumable Product',
            'type': 'consu',
        })
        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        cls.picking_type = cls.env['stock.picking.type'].search([
            ('warehouse_id', '=', cls.warehouse.id),
            ('code', '=', 'outgoing'),
        ], limit=1)
        cls.picking = cls.env['stock.picking'].create({
            'picking_type_id': cls.picking_type.id,
            'location_id': cls.picking_type.default_location_src_id.id,
            'location_dest_id': cls.picking_type.default_location_dest_id.id,
        })

    def test_action_add_to_picking_without_context_picking(self):
        """Test action_add_to_picking opens wizard when no picking in context."""
        res = self.product.action_add_to_picking()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get('res_model'), 'wizard.add.to.draft.picking')
        self.assertEqual(res.get('target'), 'new')
        self.assertEqual(res.get('context', {}).get('default_product_id'), self.product.id)

    def test_action_add_to_picking_with_context_picking(self):
        """Test action_add_to_picking directly adds or increments moves."""
        # 1. First addition: creates move with qty 1
        self.product.with_context(picking_id=self.picking.id).action_add_to_picking()
        move = self.picking.move_ids.filtered(lambda m: m.product_id == self.product)
        self.assertTrue(move, "Move should be created in picking")
        self.assertEqual(move.product_uom_qty, 1.0)

        # 2. Second addition: increments move qty to 2
        self.product.with_context(picking_id=self.picking.id).action_add_to_picking()
        self.assertEqual(move.product_uom_qty, 2.0)

    def test_action_view_details(self):
        """Test action_view_details returns wizard action with correct context."""
        action = self.product.with_context(picking_id=self.picking.id).action_view_details()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'transfer.products.details')
        self.assertEqual(action.get('view_mode'), 'form')
        self.assertEqual(action.get('target'), 'new')
        self.assertNotIn('view_type', action, "Deprecated view_type must not be present")
        self.assertEqual(action.get('context', {}).get('default_picking_id'), self.picking.id)
        self.assertEqual(action.get('context', {}).get('default_product_id'), self.product.id)
