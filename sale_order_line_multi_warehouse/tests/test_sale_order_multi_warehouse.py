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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrderLineMultiWarehouse(TransactionCase):
    """Test suite for sale order lines with multiple warehouses."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer Multi WH',
            'email': 'customer_multi_wh@example.com',
        })
        cls.warehouse_1 = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.company.id),
        ], limit=1)

        cls.warehouse_2 = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.company.id),
            ('id', '!=', cls.warehouse_1.id),
        ], limit=1)
        if not cls.warehouse_2:
            cls.warehouse_2 = cls.env['stock.warehouse'].create({
                'name': 'Second Test Warehouse',
                'code': 'WH2T',
                'company_id': cls.company.id,
            })

        cls.product_a = cls.env['product.product'].create({
            'name': 'Storable Product A',
            'is_storable': True,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Storable Product B',
            'is_storable': True,
        })

    def test_multi_warehouse_lines_create_separate_pickings(self):
        """Test that sale order lines assigned to different warehouses
        generate separate stock pickings for each warehouse upon confirmation.
        """
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_qty': 5,
                    'product_warehouse_id': self.warehouse_1.id,
                }),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'product_uom_qty': 3,
                    'product_warehouse_id': self.warehouse_2.id,
                }),
            ],
        })
        line_a = sale_order.order_line.filtered(
            lambda sol: sol.product_id == self.product_a,
        )
        line_b = sale_order.order_line.filtered(
            lambda sol: sol.product_id == self.product_b,
        )
        self.assertEqual(line_a.warehouse_id, self.warehouse_1)
        self.assertEqual(line_b.warehouse_id, self.warehouse_2)

        sale_order.action_confirm()

        self.assertEqual(len(sale_order.picking_ids), 2)
        picking_wh1 = sale_order.picking_ids.filtered(
            lambda sp: sp.picking_type_id.warehouse_id == self.warehouse_1,
        )
        picking_wh2 = sale_order.picking_ids.filtered(
            lambda sp: sp.picking_type_id.warehouse_id == self.warehouse_2,
        )

        self.assertEqual(len(picking_wh1), 1)
        self.assertEqual(len(picking_wh2), 1)

        move_a = picking_wh1.move_ids.filtered(
            lambda sm: sm.product_id == self.product_a,
        )
        move_b = picking_wh2.move_ids.filtered(
            lambda sm: sm.product_id == self.product_b,
        )
        self.assertEqual(move_a.product_uom_qty, 5.0)
        self.assertEqual(move_b.product_uom_qty, 3.0)

    def test_fallback_to_order_warehouse_when_line_warehouse_unset(self):
        """Test that a sale order line without product_warehouse_id
        falls back to the order's default warehouse.
        """
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_qty': 4,
                    'product_warehouse_id': False,
                }),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'product_uom_qty': 2,
                    'product_warehouse_id': self.warehouse_2.id,
                }),
            ],
        })
        line_a = sale_order.order_line.filtered(
            lambda sol: sol.product_id == self.product_a,
        )
        self.assertEqual(line_a.warehouse_id, self.warehouse_1)

        sale_order.action_confirm()

        self.assertEqual(len(sale_order.picking_ids), 2)
        picking_wh1 = sale_order.picking_ids.filtered(
            lambda sp: sp.picking_type_id.warehouse_id == self.warehouse_1,
        )
        picking_wh2 = sale_order.picking_ids.filtered(
            lambda sp: sp.picking_type_id.warehouse_id == self.warehouse_2,
        )
        self.assertEqual(len(picking_wh1), 1)
        self.assertEqual(len(picking_wh2), 1)

    def test_same_warehouse_lines_single_picking(self):
        """Test that lines configured with the same warehouse
        are grouped into a single picking for that warehouse.
        """
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_qty': 6,
                    'product_warehouse_id': self.warehouse_2.id,
                }),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'product_uom_qty': 2,
                    'product_warehouse_id': self.warehouse_2.id,
                }),
            ],
        })
        sale_order.action_confirm()

        self.assertEqual(len(sale_order.picking_ids), 1)
        picking = sale_order.picking_ids[0]
        self.assertEqual(picking.picking_type_id.warehouse_id, self.warehouse_2)
        self.assertEqual(len(picking.move_ids), 2)

    def test_procurement_values_and_compute_warehouse_id(self):
        """Test _prepare_procurement_values and _compute_warehouse_id behavior."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'warehouse_id': self.warehouse_1.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1,
                    'product_warehouse_id': self.warehouse_2.id,
                }),
            ],
        })
        line = sale_order.order_line[0]
        self.assertEqual(line.warehouse_id, self.warehouse_2)

        proc_values = line._prepare_procurement_values()
        self.assertEqual(proc_values.get('warehouse_id'), self.warehouse_2)

        # Update product_warehouse_id to warehouse_1 and verify recompute
        line.product_warehouse_id = self.warehouse_1
        self.assertEqual(line.warehouse_id, self.warehouse_1)
        proc_values_wh1 = line._prepare_procurement_values()
        self.assertEqual(proc_values_wh1.get('warehouse_id'), self.warehouse_1)
