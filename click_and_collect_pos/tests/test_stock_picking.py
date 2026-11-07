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
class TestStockPicking(TransactionCase):
    """Unit tests for the stock.picking model in click_and_collect_pos."""

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
        cls.product = cls.env['product.product'].create({
            'name': 'C&C Storable Product',
            'is_storable': True,
            'list_price': 100.0,
        })
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)
        if cls.warehouse:
            cls.env['stock.quant']._update_available_quantity(
                cls.product, cls.warehouse.lot_stock_id, 50.0)

    def test__force_validate_picking(self):
        """Test _force_validate_picking marks picking as done and delivers quantities."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id if self.warehouse else False,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2.0,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })],
        })
        order.action_confirm()

        cac_picking = order.picking_ids.filtered(lambda p: p.is_click_and_collect_order)
        self.assertTrue(cac_picking)

        self.env['stock.picking']._force_validate_picking(cac_picking)
        self.assertEqual(cac_picking.state, 'done')
        self.assertEqual(cac_picking.move_ids[0].state, 'done')

    def test_force_validate_picking(self):
        """Alias for test__force_validate_picking."""
        self.test__force_validate_picking()

    def test_action_confirmation_click(self):
        """Test action_confirmation_click validates C&C picking and updates delivered qty."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id if self.warehouse else False,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 4.0,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })],
        })
        order.action_confirm()
        line = order.order_line[0]

        res = self.env['stock.picking'].action_confirmation_click(line.id)
        self.assertTrue(res, "action_confirmation_click should return True on success")

        cac_picking = order.picking_ids.filtered(lambda p: p.is_click_and_collect_order)
        self.assertEqual(cac_picking.state, 'done')
        self.assertEqual(line.qty_delivered, 4.0)

        # Invalid line id should return False gracefully
        invalid_res = self.env['stock.picking'].action_confirmation_click(999999)
        self.assertFalse(invalid_res)

    def test_action_stock_picking(self):
        """Test action_stock_picking returns pending C&C picking details."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse.id if self.warehouse else False,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 3.0,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })],
        })
        order.action_confirm()
        line = order.order_line[0]

        records = self.env['stock.picking'].action_stock_picking(
            [line.id], pos_config_id=self.pos_config.id)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['id'], line.id)
        self.assertEqual(records[0]['order_id'], order.name)
        self.assertEqual(records[0]['partner_id'], self.partner.name)
        self.assertEqual(records[0]['product_uom_quantity'], 3.0)

        # Filter by different POS config should return empty
        other_pos = self.env['pos.config'].create({
            'name': 'Other Shop',
            'company_id': self.company.id,
        })
        records_other = self.env['stock.picking'].action_stock_picking(
            [line.id], pos_config_id=other_pos.id)
        self.assertEqual(len(records_other), 0)

    def test_action_confirmation_click_multistep(self):
        """Test action_confirmation_click validates upstream and downstream pickings in multi-step delivery."""
        warehouse_2step = self.env['stock.warehouse'].create({
            'name': '2-Step Warehouse Click',
            'code': 'WH2C',
            'company_id': self.company.id,
            'delivery_steps': 'pick_ship',
        })
        self.env['stock.quant']._update_available_quantity(
            self.product, warehouse_2step.lot_stock_id, 20.0)

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': warehouse_2step.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5.0,
                'is_click_and_collect': True,
                'pos_config_id': self.pos_config.id,
            })],
        })
        order.action_confirm()
        line = order.order_line[0]

        cac_pickings_init = order.picking_ids.filtered(lambda p: p.is_click_and_collect_order)
        self.assertEqual(len(cac_pickings_init), 1)
        self.assertTrue(any(p.state != 'done' for p in cac_pickings_init))

        # Confirm via POS cashier action
        res = self.env['stock.picking'].action_confirmation_click(line.id)
        self.assertTrue(res)

        # Both Pick and Ship pickings must be created, marked as C&C, and done
        all_cac_pickings = order.picking_ids.filtered(lambda p: p.is_click_and_collect_order)
        self.assertEqual(len(all_cac_pickings), 2)
        self.assertTrue(all(p.state == 'done' for p in all_cac_pickings))
        self.assertEqual(line.qty_delivered, 5.0)
