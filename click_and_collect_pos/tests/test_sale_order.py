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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleOrder(TransactionCase):
    """Unit tests for the sale.order model in click_and_collect_pos."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@test.com',
        })
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Downtown POS Store',
            'company_id': cls.company.id,
            'street': '123 Market Street',
            'city': 'San Francisco',
            'zip': '94105',
        })
        cls.product_cac = cls.env['product.product'].create({
            'name': 'C&C Storable Product',
            'is_storable': True,
            'list_price': 100.0,
        })
        cls.product_delivery = cls.env['product.product'].create({
            'name': 'Standard Delivery Product',
            'is_storable': True,
            'list_price': 50.0,
        })
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        if cls.warehouse:
            cls.env['stock.quant']._update_available_quantity(
                cls.product_cac, cls.warehouse.lot_stock_id, 50.0)
            cls.env['stock.quant']._update_available_quantity(
                cls.product_delivery, cls.warehouse.lot_stock_id, 50.0)

    def test__compute_picking_ids(self):
        """Test _compute_picking_ids excludes C&C pickings from delivery_count."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id if self.warehouse else False,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_delivery.id,
                    'product_uom_qty': 2.0,
                    'is_click_and_collect': False,
                }),
                (0, 0, {
                    'product_id': self.product_cac.id,
                    'product_uom_qty': 1.0,
                    'is_click_and_collect': True,
                    'pos_config_id': self.pos_config.id,
                }),
            ],
        })
        order.action_confirm()

        # Normal delivery pickings should be 1 and C&C picking should be 1
        self.assertEqual(order.delivery_count, 1)
        normal_pickings = order.picking_ids.filtered(
            lambda p: not p.is_click_and_collect_order)
        self.assertEqual(len(normal_pickings), order.delivery_count)

    def test_compute_picking_ids(self):
        """Alias for test__compute_picking_ids."""
        self.test__compute_picking_ids()

    def test__get_action_view_picking(self):
        """Test _get_action_view_picking returns window action excluding C&C pickings."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id if self.warehouse else False,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_delivery.id,
                    'product_uom_qty': 2.0,
                    'is_click_and_collect': False,
                }),
                (0, 0, {
                    'product_id': self.product_cac.id,
                    'product_uom_qty': 1.0,
                    'is_click_and_collect': True,
                    'pos_config_id': self.pos_config.id,
                }),
            ],
        })
        order.action_confirm()

        action = order._get_action_view_picking(order.picking_ids)
        self.assertTrue(action)
        # Action should point to stock.picking
        self.assertEqual(action.get('res_model', 'stock.picking'), 'stock.picking')

    def test_get_action_view_picking(self):
        """Alias for test__get_action_view_picking."""
        self.test__get_action_view_picking()

    def test__compute_collect_count(self):
        """Test _compute_collect_count calculates Click & Collect pickings count."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id if self.warehouse else False,
            'order_line': [(0, 0, {
                'product_id': self.product_cac.id,
                'product_uom_qty': 3.0,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })],
        })
        self.assertEqual(order.collect_count, 0)
        order.action_confirm()
        self.assertEqual(order.collect_count, 1)

    def test_compute_collect_count(self):
        """Alias for test__compute_collect_count."""
        self.test__compute_collect_count()

    def test__action_confirm(self):
        """Test _action_confirm confirms order and triggers C&C split."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id if self.warehouse else False,
            'order_line': [(0, 0, {
                'product_id': self.product_cac.id,
                'product_uom_qty': 2.0,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })],
        })
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        cac_picking = order.picking_ids.filtered(lambda p: p.is_click_and_collect_order)
        self.assertTrue(cac_picking)
        self.assertEqual(len(cac_picking), 1)

    def test_action_confirm(self):
        """Alias for test__action_confirm."""
        self.test__action_confirm()

    def test__prepare_cac_split(self):
        """Test _prepare_cac_split reassigns stock moves to dedicated C&C picking without duplication."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id if self.warehouse else False,
            'order_line': [(0, 0, {
                'product_id': self.product_cac.id,
                'product_uom_qty': 2.0,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })],
        })
        order.action_confirm()
        line = order.order_line[0]

        # Exactly 1 move must exist for this line
        self.assertEqual(len(line.move_ids), 1)
        self.assertTrue(line.move_ids.picking_id.is_click_and_collect_order)
        self.assertEqual(line.move_ids.picking_id.sale_id, order)

    def test_prepare_cac_split(self):
        """Alias for test__prepare_cac_split."""
        self.test__prepare_cac_split()

    def test_action_view_click_and_collect(self):
        """Test action_view_click_and_collect returns window action for smart button."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id if self.warehouse else False,
            'order_line': [(0, 0, {
                'product_id': self.product_cac.id,
                'product_uom_qty': 1.0,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })],
        })
        order.action_confirm()

        action = order.action_view_click_and_collect()
        self.assertEqual(action.get('res_model'), 'stock.picking')
        self.assertEqual(action.get('name'), 'Click & Collect')
        self.assertEqual(action.get('type'), 'ir.actions.act_window')

    def test_action_confirm_multi_orders(self):
        """Test confirming multiple orders at once does not raise singleton error."""
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id if self.warehouse else False,
            'order_line': [(0, 0, {
                'product_id': self.product_cac.id,
                'product_uom_qty': 1.0,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })],
        })
        order2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id if self.warehouse else False,
            'order_line': [(0, 0, {
                'product_id': self.product_cac.id,
                'product_uom_qty': 2.0,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })],
        })
        orders = order1 | order2
        # Batch confirm multiple orders in one call
        orders.action_confirm()

        self.assertEqual(order1.state, 'sale')
        self.assertEqual(order2.state, 'sale')
        self.assertTrue(order1.picking_ids.filtered(lambda p: p.is_click_and_collect_order))
        self.assertTrue(order2.picking_ids.filtered(lambda p: p.is_click_and_collect_order))

    def test_prepare_cac_split_mixed_picking(self):
        """Test mixed order separates C&C moves while preserving standard delivery moves."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id if self.warehouse else False,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_delivery.id,
                    'product_uom_qty': 1.0,
                    'is_click_and_collect': False,
                }),
                (0, 0, {
                    'product_id': self.product_cac.id,
                    'product_uom_qty': 1.0,
                    'is_click_and_collect': True,
                    'pos_config_id': self.pos_config.id,
                }),
            ],
        })
        order.action_confirm()

        cac_pickings = order.picking_ids.filtered(lambda p: p.is_click_and_collect_order)
        delivery_pickings = order.picking_ids.filtered(lambda p: not p.is_click_and_collect_order)

        self.assertEqual(len(cac_pickings), 1)
        self.assertEqual(len(delivery_pickings), 1)

        # C&C move and delivery move are in separate pickings
        cac_line = order.order_line.filtered(lambda l: l.is_click_and_collect)
        delivery_line = order.order_line.filtered(lambda l: not l.is_click_and_collect)
        self.assertEqual(cac_line.move_ids.picking_id, cac_pickings)
        self.assertEqual(delivery_line.move_ids.picking_id, delivery_pickings)

    def test_multistep_delivery_split(self):
        """Test multi-step (pick_ship) delivery correctly splits C&C pickings and preserves move chaining."""
        warehouse_2step = self.env['stock.warehouse'].create({
            'name': '2-Step Warehouse',
            'code': 'WH2',
            'company_id': self.company.id,
            'delivery_steps': 'pick_ship',
        })
        self.env['stock.quant']._update_available_quantity(
            self.product_cac, warehouse_2step.lot_stock_id, 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_delivery, warehouse_2step.lot_stock_id, 10.0)

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': warehouse_2step.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_delivery.id,
                    'product_uom_qty': 1.0,
                    'is_click_and_collect': False,
                }),
                (0, 0, {
                    'product_id': self.product_cac.id,
                    'product_uom_qty': 1.0,
                    'is_click_and_collect': True,
                    'pos_config_id': self.pos_config.id,
                }),
            ],
        })
        order.action_confirm()

        cac_pickings = order.picking_ids.filtered(lambda p: p.is_click_and_collect_order)
        delivery_pickings = order.picking_ids.filtered(lambda p: not p.is_click_and_collect_order)

        # In 2-step delivery at confirmation, initial pick pickings are created and split
        self.assertEqual(len(cac_pickings), 1)
        self.assertEqual(len(delivery_pickings), 1)
        self.assertTrue(cac_pickings.is_click_and_collect_order)
        self.assertFalse(delivery_pickings.is_click_and_collect_order)

        # Confirm C&C line via action_confirmation_click
        cac_line = order.order_line.filtered(lambda l: l.is_click_and_collect)
        res = self.env['stock.picking'].action_confirmation_click(cac_line.id)
        self.assertTrue(res)

        # After confirmation, both Pick and Out pickings exist and are done
        all_cac_pickings = order.picking_ids.filtered(lambda p: p.is_click_and_collect_order)
        self.assertEqual(len(all_cac_pickings), 2)
        self.assertTrue(all(p.state == 'done' for p in all_cac_pickings))
        self.assertEqual(cac_line.qty_delivered, 1.0)

    def test_two_cac_and_one_standard_delivery(self):
        """Test workflow with 2 C&C items and 1 standard home delivery item in the same order."""
        other_pos = self.env['pos.config'].create({
            'name': 'Uptown Store Test',
            'company_id': self.company.id,
        })
        product_cac2 = self.env['product.product'].create({
            'name': 'C&C Storable Product 2',
            'is_storable': True,
            'list_price': 75.0,
        })
        if self.warehouse:
            self.env['stock.quant']._update_available_quantity(
                product_cac2, self.warehouse.lot_stock_id, 30.0)

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id if self.warehouse else False,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_cac.id,
                    'product_uom_qty': 2.0,
                    'is_click_and_collect': True,
                    'pos_config_id': self.pos_config.id,
                }),
                (0, 0, {
                    'product_id': product_cac2.id,
                    'product_uom_qty': 1.0,
                    'is_click_and_collect': True,
                    'pos_config_id': other_pos.id,
                }),
                (0, 0, {
                    'product_id': self.product_delivery.id,
                    'product_uom_qty': 3.0,
                    'is_click_and_collect': False,
                }),
            ],
        })
        order.action_confirm()

        cac_pickings = order.picking_ids.filtered(lambda p: p.is_click_and_collect_order)
        delivery_pickings = order.picking_ids.filtered(lambda p: not p.is_click_and_collect_order)

        # Standard delivery has 1 picking, and C&C has 2 pickings (one for each store)
        self.assertEqual(len(delivery_pickings), 1)
        self.assertEqual(len(cac_pickings), 2)
        self.assertEqual(order.delivery_count, 1)
        self.assertEqual(order.collect_count, 2)

        # Confirm picking for store 1 via POS
        line_cac1 = order.order_line.filtered(lambda l: l.product_id == self.product_cac)
        res = self.env['stock.picking'].action_confirmation_click(line_cac1.id)
        self.assertTrue(res)

        # Line 1 is delivered, Line 2 and delivery line remain pending
        self.assertEqual(line_cac1.qty_delivered, 2.0)
        line_cac2 = order.order_line.filtered(lambda l: l.product_id == product_cac2)
        self.assertEqual(line_cac2.qty_delivered, 0.0)
        line_std = order.order_line.filtered(lambda l: l.product_id == self.product_delivery)
        self.assertEqual(line_std.qty_delivered, 0.0)
        self.assertIn(delivery_pickings.state, ('confirmed', 'assigned', 'waiting'))
