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
from unittest.mock import patch

from odoo.fields import Command
from odoo.tests import HttpCase, tagged
from odoo.addons.website_sale.tests.common import WebsiteSaleCommon
from odoo.addons.website_multi_variant.controllers.website_multi_variant import (
    WebsiteVariantSale,
)


@tagged('post_install', '-at_install')
class TestWebsiteMultiVariant(WebsiteSaleCommon, HttpCase):
    """Test suite for Website Multi Variant Add to Cart functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = WebsiteVariantSale()

        # Create product attribute and values for variant generation
        cls.attribute_color = cls.env['product.attribute'].create({
            'name': 'Color',
            'sequence': 1,
            'create_variant': 'always',
        })
        cls.attr_val_red = cls.env['product.attribute.value'].create({
            'name': 'Red',
            'attribute_id': cls.attribute_color.id,
            'sequence': 1,
        })
        cls.attr_val_blue = cls.env['product.attribute.value'].create({
            'name': 'Blue',
            'attribute_id': cls.attribute_color.id,
            'sequence': 2,
        })

        # Create multi-variant product template
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Test Multi Variant T-Shirt',
            'list_price': 50.0,
            'sale_ok': True,
            'is_published': True,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': cls.attribute_color.id,
                    'value_ids': [Command.set([cls.attr_val_red.id, cls.attr_val_blue.id])],
                }),
            ],
        })

        # Retrieve the generated variants
        cls.variants = cls.product_tmpl.product_variant_ids
        assert len(cls.variants) == 2, "Template should have generated 2 variants."
        cls.variant_red = cls.variants[0]
        cls.variant_blue = cls.variants[1]

        # Create unpublished multi-variant product template
        cls.unpublished_tmpl = cls.env['product.template'].create({
            'name': 'Unpublished Multi Variant',
            'list_price': 30.0,
            'sale_ok': True,
            'is_published': False,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': cls.attribute_color.id,
                    'value_ids': [Command.set([cls.attr_val_red.id])],
                }),
            ],
        })
        cls.unpublished_variant = cls.unpublished_tmpl.product_variant_ids[0]

    def test_cart_update_multi_success(self):
        """Test adding multiple variants with valid quantities to cart."""
        with self.mock_request() as request:
            post_data = {
                'product_tmpl_id': str(self.product_tmpl.id),
                f'quantity-{self.variant_red.id}': '2',
                f'quantity-{self.variant_blue.id}': '3',
            }
            response = self.controller.cart_update_multi(**post_data)

            # Should redirect to cart page
            self.assertIn(response.status_code, (302, 303))
            self.assertTrue(response.headers.get('Location', '').endswith('/shop/cart'))

            # Check cart was created and has order lines
            cart = request.cart
            self.assertTrue(cart, "Cart order should have been created.")
            self.assertEqual(len(cart.order_line), 2, "Cart should contain 2 order lines.")

            line_red = cart.order_line.filtered(lambda l: l.product_id == self.variant_red)
            line_blue = cart.order_line.filtered(lambda l: l.product_id == self.variant_blue)
            self.assertEqual(line_red.product_uom_qty, 2)
            self.assertEqual(line_blue.product_uom_qty, 3)
            self.assertEqual(cart.cart_quantity, 5)
            self.assertEqual(request.session.get('website_sale_cart_quantity'), 5)

    def test_cart_update_multi_buy_now(self):
        """Test adding variants with 'Buy Now' redirects to payment page."""
        with self.mock_request() as request:
            post_data = {
                'product_tmpl_id': str(self.product_tmpl.id),
                f'quantity-{self.variant_red.id}': '1',
                'buy_now': '1',
            }
            response = self.controller.cart_update_multi(**post_data)

            # Should redirect to payment
            self.assertIn(response.status_code, (302, 303))
            self.assertTrue(response.headers.get('Location', '').endswith('/shop/payment'))

            cart = request.cart
            self.assertTrue(cart)
            self.assertEqual(len(cart.order_line), 1)
            self.assertEqual(cart.order_line.product_id, self.variant_red)
            self.assertEqual(cart.order_line.product_uom_qty, 1)

    def test_cart_update_multi_zero_and_negative_quantities(self):
        """Test that zero, negative, and invalid quantities are ignored."""
        with self.mock_request() as request:
            post_data = {
                'product_tmpl_id': str(self.product_tmpl.id),
                f'quantity-{self.variant_red.id}': '0',
                f'quantity-{self.variant_blue.id}': '-2',
            }
            response = self.controller.cart_update_multi(**post_data)

            self.assertIn(response.status_code, (302, 303))
            self.assertTrue(response.headers.get('Location', '').endswith('/shop/cart'))

            cart = request.cart
            # Either no cart was created or cart has 0 lines
            order_lines = cart.order_line if cart else self.env['sale.order.line']
            self.assertFalse(order_lines, "Zero or negative quantities should not be added to cart.")

    def test_cart_update_multi_invalid_quantity_strings(self):
        """Test non-numeric quantity strings are gracefully handled."""
        with self.mock_request() as request:
            post_data = {
                'product_tmpl_id': str(self.product_tmpl.id),
                f'quantity-{self.variant_red.id}': 'not_a_number',
                f'quantity-{self.variant_blue.id}': '',
            }
            response = self.controller.cart_update_multi(**post_data)

            self.assertIn(response.status_code, (302, 303))
            self.assertTrue(response.headers.get('Location', '').endswith('/shop/cart'))
            cart = request.cart
            order_lines = cart.order_line if cart else self.env['sale.order.line']
            self.assertFalse(order_lines)

    def test_cart_update_multi_invalid_template_id(self):
        """Test invalid or non-existent template IDs do not cause crash."""
        with self.mock_request():
            # Non-integer template ID
            response_invalid = self.controller.cart_update_multi(
                product_tmpl_id='abc',
                **{f'quantity-{self.variant_red.id}': '1'}
            )
            self.assertIn(response_invalid.status_code, (302, 303))

            # Non-existent integer template ID
            response_nonexistent = self.controller.cart_update_multi(
                product_tmpl_id='9999999',
                **{f'quantity-{self.variant_red.id}': '1'}
            )
            self.assertIn(response_nonexistent.status_code, (302, 303))

            # Missing template ID
            response_empty = self.controller.cart_update_multi()
            self.assertIn(response_empty.status_code, (302, 303))

    def test_cart_update_multi_no_ecommerce_access(self):
        """Test redirect to /web/login when ecommerce access is denied."""
        with self.mock_request() as request:
            with patch.object(type(request.env.website), 'has_ecommerce_access', return_value=False):
                response = self.controller.cart_update_multi(
                    product_tmpl_id=str(self.product_tmpl.id),
                    **{f'quantity-{self.variant_red.id}': '1'}
                )
                self.assertIn(response.status_code, (302, 303))
                self.assertTrue(response.headers.get('Location', '').endswith('/web/login'))

    def test_cart_update_multi_existing_cart(self):
        """Test adding multiple variants when a cart already exists."""
        with self.mock_request() as request:
            # First create a cart with an existing product
            cart = self.website._create_cart()
            cart._cart_add(product_id=self.variant_red.id, quantity=1)
            self.assertEqual(cart.cart_quantity, 1)

            # Now submit multi-variant form adding more of variant_red and some variant_blue
            post_data = {
                'product_tmpl_id': str(self.product_tmpl.id),
                f'quantity-{self.variant_red.id}': '2',
                f'quantity-{self.variant_blue.id}': '3',
            }
            response = self.controller.cart_update_multi(**post_data)
            self.assertIn(response.status_code, (302, 303))

            # Variant red should now have 1 + 2 = 3, variant blue should have 3
            line_red = cart.order_line.filtered(lambda l: l.product_id == self.variant_red)
            line_blue = cart.order_line.filtered(lambda l: l.product_id == self.variant_blue)
            self.assertEqual(line_red.product_uom_qty, 3)
            self.assertEqual(line_blue.product_uom_qty, 3)
            self.assertEqual(cart.cart_quantity, 6)

    def test_cart_update_multi_unpublished_product(self):
        """Test variants of unpublished product cannot be added to cart."""
        with self.mock_request() as request:
            post_data = {
                'product_tmpl_id': str(self.unpublished_tmpl.id),
                f'quantity-{self.unpublished_variant.id}': '1',
            }
            response = self.controller.cart_update_multi(**post_data)
            self.assertIn(response.status_code, (302, 303))
            cart = request.cart
            order_lines = cart.order_line if cart else self.env['sale.order.line']
            self.assertFalse(order_lines, "Unpublished variants must not be added to cart.")

    def test_cart_update_multi_partially_paid_cart(self):
        """Test cart mutation fails when an active payment transaction exists."""
        from odoo.exceptions import UserError
        with self.mock_request():
            cart = self.website._create_cart()
            # Mock _check_not_partially_paid raising UserError
            with patch.object(type(cart), '_check_not_partially_paid', side_effect=UserError("Cart is paid")):
                with self.assertRaises(UserError):
                    self.controller.cart_update_multi(
                        product_tmpl_id=str(self.product_tmpl.id),
                        **{f'quantity-{self.variant_red.id}': '1'}
                    )


