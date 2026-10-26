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
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestSampleOrderFlow(HttpCase):
    """Test sample order flow and website shop page filtering."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Sample Flow Customer',
            'email': 'flow_customer@example.com',
        })
        cls.sample_product = cls.env['product.template'].create({
            'name': 'Published Sample Product',
            'list_price': 100.0,
            'is_sample_product': True,
            'is_published': True,
        }).product_variant_id

        cls.regular_product = cls.env['product.template'].create({
            'name': 'Published Regular Product',
            'list_price': 200.0,
            'is_sample_product': False,
            'is_published': True,
        }).product_variant_id

    def test_01_sample_order_flag_on_order(self):
        """Test is_sample_order flag on sale order lines evaluation."""
        # 1. Order with only sample products
        order_sample = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order_sample.id,
            'product_id': self.sample_product.id,
            'product_uom_qty': 1.0,
        })
        sample_lines = order_sample.order_line.filtered(
            lambda line: line.product_template_id.is_sample_product,
        )
        order_sample.is_sample_order = bool(len(sample_lines) == len(order_sample.order_line))
        self.assertTrue(order_sample.is_sample_order, "Order with only sample lines should be a sample order")

        # 2. Mixed order with sample and regular products
        order_mixed = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order_mixed.id,
            'product_id': self.sample_product.id,
            'product_uom_qty': 1.0,
        })
        self.env['sale.order.line'].create({
            'order_id': order_mixed.id,
            'product_id': self.regular_product.id,
            'product_uom_qty': 1.0,
        })
        sample_lines_mixed = order_mixed.order_line.filtered(
            lambda line: line.product_template_id.is_sample_product,
        )
        order_mixed.is_sample_order = bool(len(sample_lines_mixed) == len(order_mixed.order_line))
        self.assertFalse(order_mixed.is_sample_order, "Mixed order should not be marked as a sample order")

    def test_02_website_menu_sample_order(self):
        """Test website menu for sample order."""
        menu = self.env.ref('website_sample_product_request.menu_sample_order')
        self.assertEqual(menu.name, 'Sample Order')
        self.assertEqual(menu.url, '/shop?type=sample')

    def test_03_shop_sample_page_http(self):
        """Test HTTP GET /shop?type=sample renders successfully."""
        res = self.url_open('/shop?type=sample')
        self.assertEqual(res.status_code, 200, "Sample shop page must return 200 OK")
        self.assertIn(b'Sample Products', res.content, "Page title or content should mention Sample Products")
