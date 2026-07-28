# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
###############################################################################
from odoo.tests.common import TransactionCase

class TestMultipleWarehouseSaleOrderLine(TransactionCase):
    """Test case for multiple warehouses in sale order lines."""

    def _get_storable_type_value(self):
        """
        Detect the correct 'storable product' type value for this Odoo version.
        """

        field = self.env['product.template']._fields.get('type')
        if field:
            valid = [k for k, _ in (
                field.selection if isinstance(field.selection, list)
                else field._description_selection(self.env)
            )]
            for candidate in ('product', 'storable'):
                if candidate in valid:
                    return candidate

        tmpl = self.env['product.template'].search(
            [('type', '!=', 'service')], limit=1
        )
        if tmpl:
            return tmpl.type

        return 'consu'

    def setUp(self):
        super().setUp()

        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
        })

        self.warehouse_1 = self.env['stock.warehouse'].search([], limit=1)

        self.warehouse_2 = self.env['stock.warehouse'].create({
            'name': 'Secondary Warehouse',
            'code': 'SWH',
        })

        storable_type = self._get_storable_type_value()

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': storable_type,
            'list_price': 100,
        })

        self.consumable_product = self.env['product.product'].create({
            'name': 'Consumable Product',
            'type': 'consu',
            'list_price': 50,
        })

        self.service_product = self.env['product.product'].create({
            'name': 'Service Product',
            'type': 'service',
            'list_price': 200,
        })

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })

    def test_picking_created_on_confirm(self):
        """A picking should be created after confirming a sale order."""

        self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 5,
            'price_unit': 100,
            'product_warehouse_id': self.warehouse_2.id,
            'name': self.product.name,
        })

        self.sale_order.action_confirm()

        picking = self.sale_order.picking_ids.filtered(
            lambda p: p.state not in ['cancel']
        )

        self.assertTrue(
            picking,
            "At least one picking should be created after confirming."
        )

    def test_multiple_lines_different_warehouses(self):
        """
        Two lines with different warehouses should create separate pickings.
        """

        self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 2,
            'price_unit': 100,
            'product_warehouse_id': self.warehouse_1.id,
            'name': self.product.name,
        })

        self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 3,
            'price_unit': 100,
            'product_warehouse_id': self.warehouse_2.id,
            'name': self.product.name,
        })

        self.sale_order.action_confirm()

        active_pickings = self.sale_order.picking_ids.filtered(
            lambda p: p.state not in ['cancel']
        )

        warehouses_used = active_pickings.mapped(
            'picking_type_id.warehouse_id'
        )

        self.assertIn(
            self.warehouse_1,
            warehouses_used,
            "Warehouse 1 should have an associated picking."
        )

        self.assertIn(
            self.warehouse_2,
            warehouses_used,
            "Warehouse 2 should have an associated picking."
        )

    def test_action_launch_stock_rule_returns_true(self):
        """_action_launch_stock_rule should return True on success."""

        sale_line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 5,
            'price_unit': 100,
            'product_warehouse_id': self.warehouse_2.id,
            'name': self.product.name,
        })

        self.sale_order.action_confirm()

        sale_line.product_uom_qty = 8
        result = sale_line._action_launch_stock_rule()

        self.assertTrue(
            result,
            "_action_launch_stock_rule should return True."
        )
