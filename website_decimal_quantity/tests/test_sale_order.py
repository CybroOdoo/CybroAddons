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
from odoo.fields import Command
from odoo.tests import tagged
from odoo.addons.website_sale.tests.common import WebsiteSaleCommon


@tagged('post_install', '-at_install')
class TestSaleOrder(WebsiteSaleCommon):
    """Test cases for the 'sale.order' model functions in website_decimal_quantity."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.decimal_product = cls.env['product.product'].create({
            'name': 'Decimal Test Product',
            'sale_ok': True,
            'website_published': True,
            'lst_price': 50.0,
            'standard_price': 30.0,
            'type': 'consu',
        })
    def test__compute_cart_info(self):
        """Test _compute_cart_info computes decimal cart_quantity and only_services correctly."""
        # 1. Test empty cart has 0.0 cart_quantity
        empty_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'website_id': self.website.id,
        })
        empty_order._compute_cart_info()
        self.assertEqual(empty_order.cart_quantity, 0.0)
        # 2. Test cart with decimal quantities
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'website_id': self.website.id,
            'order_line': [
                Command.create({
                    'product_id': self.decimal_product.id,
                    'product_uom_qty': 2.5,
                }),
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.2,
                }),
            ],
        })
        order._compute_cart_info()
        # 2.5 + 1.2 = 3.7
        self.assertEqual(order.cart_quantity, 3.7)
        self.assertFalse(order.only_services)
        # 3. Test cart with only services
        service_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'website_id': self.website.id,
            'order_line': [
                Command.create({
                    'product_id': self.service_product.id,
                    'product_uom_qty': 3.5,
                }),
            ],
        })
        service_order._compute_cart_info()
        self.assertEqual(service_order.cart_quantity, 3.5)
        self.assertTrue(service_order.only_services)
    test_compute_cart_info = test__compute_cart_info

    def test__cart_add(self):
        """Test _cart_add correctly adds products with decimal quantities."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'website_id': self.website.id,
        })
        # 1. Add product with decimal quantity
        res = order._cart_add(
            product_id=self.decimal_product.id,
            quantity=2.75,
            uom_id=self.decimal_product.uom_id.id,
        )
        self.assertEqual(res['quantity'], 2.75)
        self.assertEqual(res['added_qty'], 2.75)
        self.assertTrue(res['line_id'])
        line = self.env['sale.order.line'].browse(res['line_id'])
        self.assertEqual(line.product_uom_qty, 2.75)
        # 2. Add more quantity to existing product line (triggers existing_sol branch)
        res_update = order._cart_add(
            product_id=self.decimal_product.id,
            quantity=1.25,
            uom_id=self.decimal_product.uom_id.id,
        )
        self.assertEqual(res_update['quantity'], 4.0)
        self.assertEqual(line.product_uom_qty, 4.0)
        # 3. Add with uom_id=None to verify default UoM fallback
        res_no_uom = order._cart_add(
            product_id=self.product.id,
            quantity=0.5,
            uom_id=None,
        )
        self.assertEqual(res_no_uom['quantity'], 0.5)
        self.assertEqual(res_no_uom['added_qty'], 0.5)
    test_cart_add = test__cart_add

    def test__cart_update_line_quantity(self):
        """Test _cart_update_line_quantity updates, removes, or warns appropriately."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'website_id': self.website.id,
            'order_line': [
                Command.create({
                    'product_id': self.decimal_product.id,
                    'product_uom_qty': 2.0,
                }),
            ],
        })
        line = order.order_line[0]
        # 1. Update line quantity to decimal value
        res = order._cart_update_line_quantity(line_id=line.id, quantity=4.6)
        self.assertEqual(res['quantity'], 4.6)
        self.assertEqual(line.product_uom_qty, 4.6)
        # 2. Update line quantity to 0 (line should be removed)
        res_zero = order._cart_update_line_quantity(line_id=line.id, quantity=0)
        self.assertEqual(res_zero['quantity'], 0)
        self.assertFalse(line.exists())
        # 3. Update non-existing line id returns warning
        res_invalid = order._cart_update_line_quantity(line_id=999999, quantity=1.0)
        self.assertIn('warning', res_invalid)
    test_cart_update_line_quantity = test__cart_update_line_quantity
