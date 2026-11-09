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
"""Unit tests for the sale.return and return.order.line models."""
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleReturn(TransactionCase):
    """Test cases for return order business logic and lifecycle."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Return Customer',
            'email': 'return_customer@example.com',
        })
        cls.product_a = cls.env['product.product'].create({
            'name': 'Returnable Product A',
            'type': 'consu',
            'list_price': 100.0,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Returnable Product B',
            'type': 'consu',
            'list_price': 50.0,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                Command.create({
                    'product_id': cls.product_a.id,
                    'product_uom_qty': 5,
                    'price_unit': 100.0,
                    'qty_delivered': 5,
                }),
                Command.create({
                    'product_id': cls.product_b.id,
                    'product_uom_qty': 3,
                    'price_unit': 50.0,
                    'qty_delivered': 3,
                }),
            ],
        })
        cls.sale_order.action_confirm()

        # Prepare warehouse & locations for stock delivery
        cls.warehouse = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.env.company.id)
        ], limit=1)
        cls.picking_type_out = cls.warehouse.out_type_id
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref('stock.stock_location_customers')

        # Create simulated delivery picking linked to sale order
        cls.delivery_picking = cls.env['stock.picking'].create({
            'partner_id': cls.partner.id,
            'picking_type_id': cls.picking_type_out.id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
            'origin': cls.sale_order.name,
            'move_ids': [
                Command.create({
                    'product_id': cls.product_a.id,
                    'product_uom_qty': 5,
                    'location_id': cls.stock_location.id,
                    'location_dest_id': cls.customer_location.id,
                    'sale_line_id': cls.sale_order.order_line[0].id,
                }),
                Command.create({
                    'product_id': cls.product_b.id,
                    'product_uom_qty': 3,
                    'location_id': cls.stock_location.id,
                    'location_dest_id': cls.customer_location.id,
                    'sale_line_id': cls.sale_order.order_line[1].id,
                }),
            ],
        })
        cls.delivery_picking.action_confirm()
        cls.delivery_picking.action_assign()
        for move in cls.delivery_picking.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        cls.delivery_picking.button_validate()

    def test_01_create_sale_return_defaults(self):
        """Test default values, sequence generation, report filename, and access URL."""
        return_order = self.env['sale.return'].create({
            'sale_order_id': self.sale_order.id,
            'partner_id': self.partner.id,
        })
        self.assertTrue(return_order.name, "Return order should be automatically assigned a name from sequence")
        self.assertEqual(return_order.state, 'draft', "Initial state must be 'draft'")
        self.assertTrue(return_order.active, "Return order should be active by default")
        self.assertEqual(return_order.user_id, self.env.user, "Default responsible user should be the current user")
        self.assertEqual(
            return_order._get_report_base_filename(),
            f"Sale Return - {return_order.name}",
            "Report base filename must match expected format",
        )
        self.assertEqual(
            return_order.access_url,
            f"/my/return_orders/{return_order.id}",
            "Access URL must match customer portal path",
        )

    def test_02_onchange_sale_order_and_source_pick_ids(self):
        """Test onchange updates partner_id and computes correct domain filters."""
        return_order = self.env['sale.return'].new({
            'sale_order_id': self.sale_order.id,
            'source_pick_ids': [Command.link(self.delivery_picking.id)],
        })
        res = return_order.onchange_sale_order_id_source_pick_ids()
        self.assertEqual(
            return_order.partner_id,
            self.sale_order.partner_id,
            "Partner must be updated from the selected sale order",
        )
        self.assertIn('domain', res)
        self.assertIn('source_pick_ids', res['domain'])
        self.assertIn('product_id', res['domain'])

    def test_03_onchange_product_id(self):
        """Test onchange_product_id on return.order.line with order_id in context."""
        self.sale_order.order_line[0].qty_delivered = 5.0
        line = self.env['return.order.line'].with_context(order_id=self.sale_order.id).new({
            'product_id': self.product_a.id,
        })
        res = line.onchange_product_id()
        self.assertEqual(line.quantity, 5.0, "Delivered quantity must reflect qty_delivered from sale order line")
        self.assertIn('domain', res)
        self.assertIn('product_id', res['domain'])
        self.assertIn(self.product_a.id, res['domain']['product_id'][0][2])

    def test_04_action_return_confirm(self):
        """Test action_return_confirm generates a return picking and updates lines and SO."""
        return_order = self.env['sale.return'].create({
            'sale_order_id': self.sale_order.id,
            'partner_id': self.partner.id,
            'source_pick_ids': [Command.link(self.delivery_picking.id)],
            'return_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'quantity': 5.0,
                    'received_qty': 2.0,
                    'reason': 'Product damaged during transit',
                }),
            ],
        })
        return_order.action_return_confirm()

        self.assertEqual(return_order.state, 'confirm', "State should transition to 'confirm'")
        self.assertTrue(return_order.stock_picking_ids, "Return picking should be generated and linked")

        return_pick = return_order.stock_picking_ids[0]
        self.assertTrue(return_pick.return_order_picking, "Flag return_order_picking must be set to True")
        self.assertEqual(return_pick.return_order_pick_id, return_order, "Picking should link back to return order")
        self.assertIn('Product damaged during transit', return_pick.note or '', "Picking note should record line reasons")

        # Returned move must only be for product_a with qty 2.0
        returned_products = return_pick.move_ids.mapped('product_id')
        self.assertIn(self.product_a, returned_products)
        self.assertNotIn(self.product_b, returned_products)
        move_a = return_pick.move_ids.filtered(lambda m: m.product_id == self.product_a)
        self.assertEqual(move_a.product_uom_qty, 2.0)

        # Check sale order line return_order_line_count updated
        sol_a = self.sale_order.order_line.filtered(lambda l: l.product_id == self.product_a)
        self.assertEqual(sol_a.return_order_line_count, 2)

    def test_05_action_return_cancel(self):
        """Test action_return_cancel cancels the return order and associated pickings."""
        return_order = self.env['sale.return'].create({
            'sale_order_id': self.sale_order.id,
            'partner_id': self.partner.id,
            'source_pick_ids': [Command.link(self.delivery_picking.id)],
            'return_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'quantity': 5.0,
                    'received_qty': 1.0,
                    'reason': 'Customer changed mind',
                }),
            ],
        })
        return_order.action_return_confirm()
        return_pick = return_order.stock_picking_ids[0]
        self.assertNotEqual(return_pick.state, 'cancel')

        return_order.action_return_cancel()
        self.assertEqual(return_order.state, 'cancel', "Return order state should be 'cancel'")
        self.assertEqual(return_pick.state, 'cancel', "Associated picking should be cancelled")

    def test_06_compute_delivery_and_picking_count(self):
        """Test compute method for delivery_count and picking_count."""
        return_order = self.env['sale.return'].create({
            'sale_order_id': self.sale_order.id,
            'partner_id': self.partner.id,
            'source_pick_ids': [Command.link(self.delivery_picking.id)],
        })
        return_order._compute_delivery()
        self.assertEqual(return_order.delivery_count, 1)
        self.assertEqual(return_order.picking_count, 0)

        # Create return picking manually
        return_pick = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.warehouse.in_type_id.id,
            'location_id': self.customer_location.id,
            'location_dest_id': self.stock_location.id,
            'return_order_pick_id': return_order.id,
            'return_order_picking': True,
        })
        return_order._compute_delivery()
        self.assertEqual(return_order.picking_count, 1)

    def test_07_action_view_picking_and_delivery(self):
        """Test action_view_picking and action_view_delivery return appropriate action dicts."""
        return_order = self.env['sale.return'].create({
            'sale_order_id': self.sale_order.id,
            'partner_id': self.partner.id,
            'source_pick_ids': [Command.link(self.delivery_picking.id)],
        })
        # Test delivery view action
        delivery_action = return_order.action_view_delivery()
        self.assertEqual(delivery_action.get('res_id'), self.delivery_picking.id)
        self.assertEqual(delivery_action.get('context', {}).get('default_partner_id'), self.partner.id)

        # Test picking view action with return picking
        return_pick = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.customer_location.id,
            'location_dest_id': self.stock_location.id,
            'return_order_pick_id': return_order.id,
            'return_order_picking': True,
        })
        picking_action = return_order.action_view_picking()
        self.assertEqual(picking_action.get('res_id'), return_pick.id)
        self.assertEqual(picking_action.get('context', {}).get('default_partner_id'), self.partner.id)

    def test_08_action_return_confirm_no_pickings(self):
        """Test action_return_confirm when no source picking exists for the sale order."""
        empty_so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        return_order = self.env['sale.return'].create({
            'sale_order_id': empty_so.id,
            'partner_id': self.partner.id,
        })
        # When no stock pickings exist, action_return_confirm should not crash
        return_order.action_return_confirm()
        self.assertEqual(return_order.state, 'draft', "State remains draft if no pickings exist to return")
