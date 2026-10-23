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
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestStockMove(TransactionCase):
    """Test cases for stock.move model in delivery_split module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']
        cls.SaleOrder = cls.env['sale.order']
        cls.StockMove = cls.env['stock.move']

        cls.customer = cls.Partner.create({
            'name': 'Primary Customer',
            'email': 'customer@test.com',
        })
        cls.recipient_a = cls.Partner.create({
            'name': 'Recipient Alpha',
            'email': 'alpha@test.com',
        })
        cls.recipient_b = cls.Partner.create({
            'name': 'Recipient Beta',
            'email': 'beta@test.com',
        })

        cls.product_a = cls.Product.create({
            'name': 'Product Alpha',
            'is_storable': True,
            'list_price': 100.0,
        })
        cls.product_b = cls.Product.create({
            'name': 'Product Beta',
            'is_storable': True,
            'list_price': 120.0,
        })
        cls.product_c = cls.Product.create({
            'name': 'Product Gamma',
            'is_storable': True,
            'list_price': 80.0,
        })

    def test_key_assign_picking_split_no_consolidate(self):
        """Test _key_assign_picking adds order and move IDs when is_consolidate is False."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': True,
            'is_consolidate': False,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'recipient_id': self.recipient_a.id,
                }),
            ],
        })
        order.action_confirm()

        move = order.order_line[0].move_ids
        self.assertTrue(move, "Stock move should be generated upon order confirmation.")

        keys = move._key_assign_picking()
        self.assertIn(order.id, keys, "Order ID should be included in picking assign keys.")
        self.assertIn(move.id, keys, "Move ID should be included in keys when not consolidated.")

    def test_key_assign_picking_split_with_consolidate(self):
        """Test _key_assign_picking adds order and recipient IDs when is_consolidate is True."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': True,
            'is_consolidate': True,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'recipient_id': self.recipient_a.id,
                }),
            ],
        })
        order.action_confirm()

        move = order.order_line[0].move_ids
        self.assertTrue(move, "Stock move should be generated upon order confirmation.")

        keys = move._key_assign_picking()
        self.assertIn(order.id, keys, "Order ID should be included in picking assign keys.")
        self.assertIn(self.recipient_a.id, keys, "Recipient ID should be included in keys when consolidated.")
        self.assertNotIn(move.id, keys, "Move ID should not be in keys when consolidated.")

    def test_search_picking_for_assignation_split_no_consolidate(self):
        """Test _search_picking_for_assignation returns an empty recordset when is_consolidate is False."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': True,
            'is_consolidate': False,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'recipient_id': self.recipient_a.id,
                }),
            ],
        })
        order.action_confirm()

        move = order.order_line[0].move_ids
        picking = move._search_picking_for_assignation()
        self.assertFalse(picking, "Should return empty picking recordset so a new picking is created for each move.")

    def test_split_delivery_workflow_separate_pickings(self):
        """Test confirming a sale order with delivery split creates distinct pickings per recipient."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': True,
            'is_consolidate': False,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 2.0,
                    'recipient_id': self.recipient_a.id,
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'product_uom_qty': 3.0,
                    'recipient_id': self.recipient_b.id,
                }),
            ],
        })

        order.action_confirm()
        self.assertEqual(len(order.picking_ids), 2, "Two distinct pickings should be created for two different recipients.")

        picking_partners = order.picking_ids.mapped('partner_id')
        self.assertIn(self.recipient_a, picking_partners, "One picking must be assigned to Recipient Alpha.")
        self.assertIn(self.recipient_b, picking_partners, "One picking must be assigned to Recipient Beta.")

    def test_split_delivery_workflow_consolidated_pickings(self):
        """Test confirming a sale order with consolidation merges lines sharing the same recipient."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': True,
            'is_consolidate': True,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'recipient_id': self.recipient_a.id,
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'product_uom_qty': 2.0,
                    'recipient_id': self.recipient_a.id,
                }),
                Command.create({
                    'product_id': self.product_c.id,
                    'product_uom_qty': 3.0,
                    'recipient_id': self.recipient_b.id,
                }),
            ],
        })

        order.action_confirm()
        self.assertEqual(
            len(order.picking_ids),
            2,
            "Three order lines with two unique recipients should consolidate into two pickings.",
        )

        picking_alpha = order.picking_ids.filtered(lambda p: p.partner_id == self.recipient_a)
        picking_beta = order.picking_ids.filtered(lambda p: p.partner_id == self.recipient_b)

        self.assertEqual(len(picking_alpha), 1, "Exactly one picking should exist for Recipient Alpha.")
        self.assertEqual(len(picking_alpha.move_ids), 2, "Recipient Alpha picking should contain two consolidated moves.")

        self.assertEqual(len(picking_beta), 1, "Exactly one picking should exist for Recipient Beta.")
        self.assertEqual(len(picking_beta.move_ids), 1, "Recipient Beta picking should contain one move.")

    def test_standard_delivery_without_split(self):
        """Test confirming a sale order without delivery split creates a single standard picking."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': False,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'product_uom_qty': 2.0,
                }),
            ],
        })

        order.action_confirm()
        self.assertEqual(len(order.picking_ids), 1, "A single picking should be created when delivery split is disabled.")
        self.assertEqual(
            order.picking_ids.partner_id,
            self.customer,
            "Picking partner should be the order customer when delivery split is disabled.",
        )
