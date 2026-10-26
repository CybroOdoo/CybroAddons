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
from odoo.tests.common import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestProductWebHover(TransactionCase):
    """Test suite for Product Web Hover view and model integrations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Hover Test Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Hover Popover Test Product',
            'is_storable': True,
            'list_price': 49.99,
        })
        cls.salesman = new_test_user(
            cls.env, login='hover_salesman', groups='sales_team.group_sale_salesman')

    def test_view_order_form_inheritance(self):
        """The sale order form includes the hover widget on the order lines."""
        view = self.env.ref('product_web_hover.sale_order_view_form_product_web_hover')
        arch = self.env['sale.order'].get_view(view.inherit_id.id, 'form')['arch']
        self.assertIn('product_detail_popover_widget', arch)
        self.assertIn('product_and_description', arch)
        widget_idx = arch.index('product_detail_popover_widget')
        col_idx = arch.index('name="product_and_description"')
        self.assertLess(widget_idx, col_idx, "Widget must precede the product_and_description column")

    def test_stock_module_installed(self):
        """The popover reads qty_available, which is defined by `stock`."""
        self.assertIn('qty_available', self.env['product.product']._fields)
        module = self.env['ir.module.module'].search(
            [('name', '=', 'stock')])
        self.assertEqual(module.state, 'installed')

    def test_popover_fields_readable_by_salesman(self):
        """The fields requested by the popover can be read by a salesman."""
        self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': self.product.id,
            'location_id': self.env['stock.warehouse'].search([], limit=1).lot_stock_id.id,
            'inventory_quantity': 5,
        }).action_apply_inventory()
        product = self.product.with_user(self.salesman)
        data = product.read(
            ['name', 'categ_id', 'default_code', 'qty_available'])[0]
        self.assertEqual(data['qty_available'], 5.0)
        self.assertEqual(data['name'], 'Hover Popover Test Product')

    def test_sale_order_line_product_data(self):
        """Order lines expose the product, quantity and price used by the card."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2,
            })],
        })
        line = order.order_line[0]
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.price_unit, 49.99)
        self.assertEqual(line.product_uom_qty, 2)
