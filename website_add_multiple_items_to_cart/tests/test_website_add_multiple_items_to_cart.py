# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (https://www.cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.website.tools import MockRequest
from odoo.addons.website_add_multiple_items_to_cart.controllers.website_add_multiple_items_to_cart import (
    WebsiteAddMultiProduct,
)



@tagged('post_install', '-at_install')
class TestWebsiteAddMultipleItemsToCart(TransactionCase):
    """Test cases for the WebsiteAddMultiProduct controller.

    Uses MockRequest (no real HTTP server / no websocket) so teardown
    is clean and test execution is fast.

    Key design note
    ---------------
    MockRequest creates a *fresh* session dict for every ``with`` block.
    ``website.sale_get_order()`` locates (or creates) the cart via
    ``request.session['sale_order_id']``.  To reuse the same cart across
    multiple controller calls we capture the order-id from the first call
    and pass it back via ``MockRequest(..., sale_order_id=...)``.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Resolve the default website and its public user.
        cls.website = cls.env.company.website_id
        if not cls.website:
            cls.website = cls.env.ref('website.default_website')
            cls.website.company_id = cls.env.company

        cls.public_user = cls.website.user_id

        # Instantiate the controller under test.
        cls.controller = WebsiteAddMultiProduct()

        # Create two published, consumable products so that
        # website_sale's _cart_update does not raise a UserError.
        cls.product_tmpl_1 = cls.env['product.template'].create({
            'name': 'Test Product 1',
            'list_price': 100.0,
            'sale_ok': True,
            'is_published': True,
            'type': 'consu',
        })
        cls.product_tmpl_2 = cls.env['product.template'].create({
            'name': 'Test Product 2',
            'list_price': 200.0,
            'sale_ok': True,
            'is_published': True,
            'type': 'consu',
        })

        # Grab the auto-created product.product variants.
        cls.product_1 = cls.product_tmpl_1.product_variant_id
        cls.product_2 = cls.product_tmpl_2.product_variant_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _make_env(self, user=None):
        """Return an env scoped to *user* (defaults to the public user)."""
        return self.env(user=user or self.public_user)

    def _call_add_multi_product(self, product_ids, sale_order_id=None,
                                website=None, user=None):
        """Invoke ``cart_add_multi_product`` inside a MockRequest context.

        Parameters
        ----------
        product_ids   : list of int  – product.product IDs to add
        sale_order_id : int | None   – pass an existing order-id to reuse
                                       the same cart across calls
        Returns
        -------
        tuple(result_dict, sale_order_id)
            *result_dict*   – the dict returned by the controller
            *sale_order_id* – the id of the cart that was used/created,
                              so it can be forwarded to the next call
        """
        website = website or self.website
        user = user or self.public_user
        env = self._make_env(user)
        with MockRequest(env,
                         website=website.with_user(user),
                         sale_order_id=sale_order_id) as mock_req:
            result = self.controller.cart_add_multi_product(
                product_ids=product_ids,
            )
            # Capture the order-id that sale_get_order stored in the session.
            used_order_id = mock_req.session.get('sale_order_id')
        return result, used_order_id

    def _call_cart_qty(self, sale_order_id=None, website=None, user=None):
        """Invoke ``cart_qty_check`` inside a MockRequest context.

        Returns
        -------
        int  – the cart quantity returned by the controller
        """
        website = website or self.website
        user = user or self.public_user
        env = self._make_env(user)
        with MockRequest(env,
                         website=website.with_user(user),
                         sale_order_id=sale_order_id):
            result = self.controller.cart_qty_check()
        return result

    # ------------------------------------------------------------------
    # test_cart_add_multi_product
    # ------------------------------------------------------------------
    def test_cart_add_multi_product(self):
        """Adding two published products must:
          - return added_qty=2
          - return total_qty=2
          - create a draft sale order containing both products
        """

        result, order_id = self._call_add_multi_product(
            product_ids=[self.product_1.id, self.product_2.id],
        )

        self.assertIsInstance(result, dict,
                              "Controller must return a dict")
        self.assertEqual(result.get('added_qty'), 2,
                         "added_qty should be 2")
        self.assertEqual(result.get('total_qty'), 2,
                         "total_qty should be 2")

        # The draft sale order must contain both products.
        self.assertTrue(order_id,
                        "A sale_order_id should have been stored in the session")
        sale_order = self.env['sale.order'].sudo().browse(order_id)
        self.assertTrue(sale_order.exists(),
                        "The sale order must exist in the database")
        self.assertEqual(sale_order.state, 'draft',
                         "The order must be in draft state")

        order_products = sale_order.order_line.mapped('product_id')
        self.assertIn(self.product_1, order_products,
                      "product_1 must be in the cart")
        self.assertIn(self.product_2, order_products,
                      "product_2 must be in the cart")
        self.assertEqual(sale_order.cart_quantity, 2,
                         "cart_quantity must equal 2")


    # ------------------------------------------------------------------
    # test_cart_add_multi_product_empty
    # ------------------------------------------------------------------
    def test_cart_add_multi_product_empty(self):
        """Calling the route with an empty product_ids list must succeed
        and return added_qty=0 (no crash, no UserError).
        """

        result, _order_id = self._call_add_multi_product(product_ids=[])

        self.assertIsInstance(result, dict,
                              "Controller must return a dict even for empty list")
        self.assertEqual(result.get('added_qty'), 0,
                         "added_qty must be 0 when product_ids is empty")

    # ------------------------------------------------------------------
    # test_cart_add_multi_product_duplicate
    # ------------------------------------------------------------------
    def test_cart_add_multi_product_duplicate(self):
        """Adding the same product twice must increment the existing
        order line (product_uom_qty == 2) rather than creating a duplicate.

        Controller logic recap:
            if order_line:
                order_line.product_uom_qty += 1   ← increment path
            else:
                sale_order._cart_update(...)       ← create path

        We forward the sale_order_id from the first call into the second
        so both calls operate on the same cart.
        """

        # First call – creates the order line (qty = 1).
        r1, order_id = self._call_add_multi_product(
            product_ids=[self.product_1.id],
        )
        self.assertEqual(r1.get('added_qty'), 1,
                         "First add should report added_qty=1")
        self.assertTrue(order_id, "order_id must be returned after first call")

        # Second call – reuses the same cart via sale_order_id.
        r2, _oid = self._call_add_multi_product(
            product_ids=[self.product_1.id],
            sale_order_id=order_id,
        )
        self.assertEqual(r2.get('added_qty'), 1,
                         "Second add should also report added_qty=1")

        # Verify the order line quantity is now 2.
        sale_order = self.env['sale.order'].sudo().browse(order_id)
        self.assertTrue(sale_order.exists(), "Draft sale order must exist")

        line = sale_order.order_line.filtered(
            lambda l: l.product_id.id == self.product_1.id
        )
        self.assertTrue(line, "Order line for product_1 must exist")
        self.assertEqual(
            line.product_uom_qty, 2,
            "Quantity should be 2 after adding the same product twice",
        )


    # ------------------------------------------------------------------
    # test_cart_qty_check
    # ------------------------------------------------------------------
    def test_cart_qty_check(self):
        """cart_qty_check must return an integer >= 1 after seeding the
        cart with at least one product.

        We forward the sale_order_id so cart_qty_check sees the same
        order that was seeded.
        """

        # Seed the cart first so there is something to count.
        seed, order_id = self._call_add_multi_product(
            product_ids=[self.product_1.id],
        )
        self.assertEqual(seed.get('added_qty'), 1,
                         "Seeding the cart should add 1 item")
        self.assertTrue(order_id, "order_id must be set after seeding")

        # Check qty using the same cart.
        cart_qty = self._call_cart_qty(sale_order_id=order_id)

        self.assertIsInstance(cart_qty, int,
                              "result of cart_qty_check must be an integer")
        self.assertGreaterEqual(cart_qty, 1,
                                "cart_qty must be at least 1 after seeding")
