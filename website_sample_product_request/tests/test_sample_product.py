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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSampleProduct(TransactionCase):
    """Test cases for sample product features and pricing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Sample Customer',
            'email': 'customer@example.com',
        })
        cls.regular_template = cls.env['product.template'].create({
            'name': 'Regular Product',
            'list_price': 150.0,
            'is_sample_product': False,
        })
        cls.sample_template = cls.env['product.template'].create({
            'name': 'Sample Product Test',
            'list_price': 75.0,
            'is_sample_product': True,
        })
        cls.regular_product = cls.regular_template.product_variant_id
        cls.sample_product = cls.sample_template.product_variant_id
        cls.website = cls.env['website'].search([], limit=1)
        cls.pricelist = cls.env['product.pricelist'].search([], limit=1)
        cls.fiscal_position = cls.env['account.fiscal.position'].search([], limit=1)

    def test_01_sample_product_flag_and_onchange(self):
        """Test is_sample_product flag and onchange setting price to 0."""
        product_tmpl = self.env['product.template'].new({
            'name': 'Test New Sample',
            'list_price': 200.0,
            'is_sample_product': True,
        })
        product_tmpl._onchange_is_sample_product()
        self.assertEqual(
            product_tmpl.list_price, 0.0,
            "Onchange must set list_price to 0.0 when is_sample_product is True",
        )

    def test_02_get_combination_info_sample_product(self):
        """Test _get_combination_info returns zero prices for sample product."""
        # For sample product
        res_sample = self.sample_template.with_context(
            website_id=self.website.id,
        )._get_combination_info(
            pricelist=self.pricelist,
            fiscal_position=self.fiscal_position,
        )
        self.assertEqual(res_sample['price'], 0.0)
        self.assertEqual(res_sample['list_price'], 0.0)
        self.assertEqual(res_sample['price_reduce'], 0.0)
        self.assertFalse(res_sample['has_discounted_price'])

        # For regular product
        res_regular = self.regular_template.with_context(
            website_id=self.website.id,
        )._get_combination_info(
            pricelist=self.pricelist,
            fiscal_position=self.fiscal_position,
        )
        self.assertEqual(res_regular['price'], 150.0)
        self.assertEqual(res_regular['list_price'], 150.0)

    def test_03_sale_order_line_display_price(self):
        """Test _get_display_price on sale order line for sample and regular products."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        line_sample = self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.sample_product.id,
            'product_uom_qty': 1.0,
        })
        line_regular = self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.regular_product.id,
            'product_uom_qty': 1.0,
        })
        self.assertEqual(
            line_sample._get_display_price(), 0.0,
            "Display price for sample product line must be 0.0",
        )
        self.assertEqual(
            line_regular._get_display_price(), 150.0,
            "Display price for regular product line must match product list price",
        )

    def test_04_actions_and_menus(self):
        """Test backend actions and domain filters for sample products and orders."""
        action_prod = self.env.ref('website_sample_product_request.product_template_action')
        self.assertEqual(action_prod.res_model, 'product.template')
        self.assertIn("('is_sample_product', '=', True)", action_prod.domain)

        action_order = self.env.ref('website_sample_product_request.sale_order_action')
        self.assertEqual(action_order.res_model, 'sale.order')
        self.assertIn("('is_sample_order', '=', True)", action_order.domain)

        menu_root = self.env.ref('website_sample_product_request.website_sample_product_request_menu_root')
        self.assertTrue(menu_root.exists(), "Sample root menu must exist")
