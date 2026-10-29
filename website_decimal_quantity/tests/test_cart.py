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
from odoo.exceptions import UserError
from odoo.tests import HttpCase, tagged
from odoo.addons.website_sale.tests.common import WebsiteSaleCommon
from odoo.addons.website_decimal_quantity.controllers.cart import CartDecimal


@tagged('post_install', '-at_install')
class TestCart(WebsiteSaleCommon, HttpCase):
    """Test cases for the 'CartDecimal' controller functions in website_decimal_quantity."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # In Odoo 20, direct calls to controller methods decorated with empty @http.route()
        # expect routing['type'] to be populated by the routing table generator.
        CartDecimal.add_to_cart.original_routing.setdefault('type', 'jsonrpc')
        CartDecimal.update_cart.original_routing.setdefault('type', 'jsonrpc')
        cls.cart_controller = CartDecimal()
        cls.decimal_product = cls.env['product.product'].create({
            'name': 'Decimal Controller Test Product',
            'sale_ok': True,
            'website_published': True,
            'lst_price': 100.0,
            'standard_price': 60.0,
        })

    def test_add_to_cart(self):
        """Test add_to_cart controller handles float quantities properly."""
        with self.mock_request(user=self.public_user) as req:
            # 1. Add float quantity to cart
            res = self.cart_controller.add_to_cart(
                product_template_id=self.decimal_product.product_tmpl_id.id,
                product_id=self.decimal_product.id,
                quantity=2.5,
            )
            self.assertEqual(res['quantity'], 2.5)
            self.assertEqual(res['cart_quantity'], 2.5)
            self.assertEqual(req.cart.cart_quantity, 2.5)
            self.assertEqual(res['currency'], req.cart.currency_id.name)
            self.assertIn('notifications', res)
            # 2. Add string float representation to cart (e.g., from form/URL)
            res_str = self.cart_controller.add_to_cart(
                product_template_id=self.decimal_product.product_tmpl_id.id,
                product_id=self.decimal_product.id,
                quantity="1.5",
            )
            self.assertEqual(res_str['quantity'], 4.0)
            self.assertEqual(res_str['cart_quantity'], 4.0)
            self.assertEqual(req.cart.cart_quantity, 4.0)
            # 3. Non-existent product raises UserError
            with self.assertRaises(UserError):
                self.cart_controller.add_to_cart(
                    product_template_id=0,
                    product_id=999999,
                    quantity=1.0,
                )

    def test_update_cart(self):
        """Test update_cart controller updates cart line with decimal quantities."""
        with self.mock_request(user=self.public_user) as req:
            # First add product to cart
            self.cart_controller.add_to_cart(
                product_template_id=self.decimal_product.product_tmpl_id.id,
                product_id=self.decimal_product.id,
                quantity=1.0,
            )
            order_line = req.cart.order_line[0]
            # 1. Update line quantity using line_id
            values = self.cart_controller.update_cart(
                line_id=order_line.id,
                quantity=3.5,
            )
            self.assertEqual(values['quantity'], 3.5)
            self.assertEqual(order_line.product_uom_qty, 3.5)
            self.assertEqual(values['cart_quantity'], 3.5)
            self.assertIn('website_sale.quick_reorder_history', values)
            # 2. Update line quantity using product_id without line_id
            values_by_product = self.cart_controller.update_cart(
                line_id=None,
                quantity=5.5,
                product_id=self.decimal_product.id,
            )
            self.assertEqual(values_by_product['quantity'], 5.5)
            self.assertEqual(order_line.product_uom_qty, 5.5)
            self.assertEqual(values_by_product['cart_quantity'], 5.5)
