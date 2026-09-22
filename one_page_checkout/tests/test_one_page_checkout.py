# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################

import odoo.tests


@odoo.tests.tagged('post_install', '-at_install')
class TestOnePageCheckout(odoo.tests.HttpCase):
    """
    Test cases for one_page_checkout functionality.
    """

    def setUp(self):

        super().setUp()

        self.product = self.env['product.template'].create({
            'name': 'Test Product for Checkout',
            'type': 'consu',
            'is_published': True,
            'sale_ok': True,
            'website_published': True,
            'list_price': 100.0,
        })

        portal_group = self.env.ref('base.group_portal')

        self.user = self.env['res.users'].create({
            'name': 'Portal Test User',
            'login': 'portal_test',
            'password': 'portal_test',
            'email': 'portal@test.com',
            'group_ids': [(6, 0, [portal_group.id])],
        })



        self.authenticate('portal_test', 'portal_test')


    def test_01_extra_info_redirect(self):
        """ Test that extra_info route redirects to /shop/payment """
        response = self.url_open('/shop/extra_info')

        self.assertEqual(
            response.status_code,
            200,
            "Response status code should be 200"
        )


        self.assertTrue(
            '/shop/payment' in response.url or '/shop/cart' in response.url,
            "Should be redirected from extra_info"
        )

    def _create_cart(self):
        website = self.env['website'].get_current_website()
        # Delete any existing carts for the user
        self.env['sale.order'].search([
            ('partner_id', '=', self.user.partner_id.id),
            ('state', '=', 'draft')
        ]).unlink()

        # Create a new cart (draft sale order)
        order = self.env['sale.order'].create({
            'partner_id': self.user.partner_id.id,
            'website_id': website.id,
            'state': 'draft',
            'order_line': [(0, 0, {
                'product_id': self.product.product_variant_id.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })]
        })
        return order

    def test_02_shop_address_redirect(self):
        """ Test that shop_address redirects properly """


        self._create_cart()

        # Open address page
        response = self.url_open('/shop/address')


        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            '/shop/payment' in response.url
            or '/shop/address' in response.url
            or '/shop/checkout' in response.url,
            f"Unexpected redirect URL: {response.url}"
        )

    def test_03_shop_payment_access(self):
        """ Test that shop_payment loads successfully """
        self._create_cart()

        # Access payment page
        response = self.url_open('/shop/payment')
        self.assertEqual(response.status_code, 200)
        # Should not be redirected back to cart if cart has products
        self.assertTrue('/shop/payment' in response.url)

