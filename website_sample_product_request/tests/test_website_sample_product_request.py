# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright(C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Shikhil (<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import MagicMock
from werkzeug.datastructures import MultiDict
from odoo.tests import tagged, TransactionCase
from odoo.addons.website.tools import MockRequest
from odoo.addons.website_sample_product_request.controllers.website_sample_product_request import TableCompute, WebsiteSaleInherit
from odoo.http import Response



@tagged('post_install', '-at_install')
class TestTableCompute(TransactionCase):

    def test_table_compute_process(self):
        """Test TableCompute grid arrangement logic for products."""
        product_1 = self.env['product.template'].create({
            'name': 'Grid Product 1',
            'website_size_x': 2,
            'website_size_y': 2,
        })
        product_2 = self.env['product.template'].create({
            'name': 'Grid Product 2',
            'website_size_x': 1,
            'website_size_y': 1,
        })

        tc = TableCompute()
        rows = tc.process([product_1, product_2], ppg=20, ppr=4)

        self.assertTrue(isinstance(rows, list))
        self.assertTrue(len(rows) > 0)


@tagged('post_install', '-at_install')
class TestWebsiteSampleProductRequestController(TransactionCase):

    def setUp(self):
        super().setUp()
        self.WebsiteSaleController = WebsiteSaleInherit()
        self.website = self.env['website'].get_current_website()

        # Create products
        self.sample_product = self.env['product.product'].create({
            'name': 'Website Sample Product',
            'is_sample_product': True,
            'website_published': True,
            'list_price': 0.0,
        })

        self.regular_product = self.env['product.product'].create({
            'name': 'Website Regular Product',
            'is_sample_product': False,
            'website_published': True,
            'list_price': 100.0,
        })

        # Create a partner and order
        self.partner = self.env['res.partner'].create({'name': 'Test Portal Customer'})
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'website_id': self.website.id,
            'is_sample_order': False,
        })

    def test_cart_controller_with_regular_product(self):
        """Test cart route sets is_sample_order=False when a regular product is in the cart."""
        # Add regular product line to the order
        self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.regular_product.id,
            'product_uom_qty': 1,
        })

        with MockRequest(self.env, website=self.website, sale_order_id=self.order.id):
            self.WebsiteSaleController.cart()
            # The controller's cart method should evaluate order_line and update is_sample_order
            self.assertFalse(self.order.is_sample_order)

    def test_cart_controller_with_sample_product(self):
        """Test cart route sets is_sample_order=True when a sample product is in the cart."""
        # Add sample product line to the order
        self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.sample_product.id,
            'product_uom_qty': 1,
        })

        with MockRequest(self.env, website=self.website, sale_order_id=self.order.id):
            self.WebsiteSaleController.cart()
            self.assertTrue(self.order.is_sample_order)

    def test_shop_controller_with_sample_type(self):
        """Test shop route when type parameter is set to 'sample'."""
        with MockRequest(self.env, website=self.website) as req:
            # Set request.httprequest.args to a MultiDict to support getlist()
            req.httprequest.args = MultiDict()

            # Create a real odoo.http.Response object as the result of the first render call
            mock_response = Response(
                template="website_sale.products",
                qcontext={
                    'products': self.env['product.template'],
                    'bins': [],
                }
            )
            req.render = MagicMock(return_value=mock_response)

            # Calling shop with type=sample
            self.WebsiteSaleController.shop(type='sample')

            # Assert req.render was called to render our template
            self.assertEqual(req.render.call_count, 2)

            # Check the second render call (which renders the sample template)
            args, kwargs = req.render.call_args
            self.assertEqual(args[0], "website_sample_product_request.sample_order_template_view")

            rendered_context = args[1] if len(args) > 1 else kwargs.get('qcontext', {})
            self.assertIn('products', rendered_context)

            # Verify only sample products are in the products variable passed to the template
            sample_products = rendered_context['products']
            self.assertTrue(any(p.id == self.sample_product.product_tmpl_id.id for p in sample_products))
            self.assertFalse(any(p.id == self.regular_product.product_tmpl_id.id for p in sample_products))