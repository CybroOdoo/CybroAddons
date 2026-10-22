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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Unit tests for top_selling_products_in_category module."""
from unittest.mock import MagicMock, patch

from odoo.tests import common, tagged
from odoo.addons.top_selling_products_in_category.controllers.top_selling_products_in_category import (
    TopSellingProducts,
)


@tagged('post_install', '-at_install')
class TestTopSellingProducts(common.TransactionCase):
    """Test top selling products retrieval, sorting, and category grouping."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        if not cls.website:
            cls.website = cls.env['website'].create({
                'name': 'Test Website',
            })

        # Create public categories
        cls.category_a = cls.env['product.public.category'].create({
            'name': 'Electronics Category',
            'sequence': 1,
        })
        cls.category_b = cls.env['product.public.category'].create({
            'name': 'Accessories Category',
            'sequence': 2,
        })

        # Create partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Customer Test',
        })

        # Product 1: High sales (qty 10) in category_a and category_b
        cls.product_high = cls.env['product.template'].create({
            'name': 'High Selling Phone',
            'is_published': True,
            'public_categ_ids': [(6, 0, [cls.category_a.id, cls.category_b.id])],
        })

        # Product 2: Medium sales (qty 3) in category_a
        cls.product_med = cls.env['product.template'].create({
            'name': 'Medium Selling Laptop',
            'is_published': True,
            'public_categ_ids': [(6, 0, [cls.category_a.id])],
        })

        # Product 3: Zero sales in category_b
        cls.product_zero = cls.env['product.template'].create({
            'name': 'Unsold Cable',
            'is_published': True,
            'public_categ_ids': [(6, 0, [cls.category_b.id])],
        })

        # Create confirmed sales to give products sales_count
        order_high = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product_high.product_variant_id.id,
                'product_uom_qty': 10,
                'price_unit': 100.0,
            })],
        })
        order_high.action_confirm()

        order_med = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product_med.product_variant_id.id,
                'product_uom_qty': 3,
                'price_unit': 50.0,
            })],
        })
        order_med.action_confirm()

        cls.controller = TopSellingProducts()

    def test_products_categories_sorting_and_filtering(self):
        """Test products are filtered by sales_count >= 1 and sorted descending."""
        mock_request = MagicMock()
        mock_request.env = self.env(context=dict(self.env.context, website_id=self.website.id))
        mock_request.website = self.website

        with patch('odoo.addons.top_selling_products_in_category.controllers.top_selling_products_in_category.request', mock_request):
            products, categories, website_id = self.controller.products_categories()

        # Website ID must be an integer (or False), not a recordset
        self.assertIsInstance(website_id, int)
        self.assertEqual(website_id, self.website.id)

        # Products with 0 sales must be excluded
        product_ids = [p['id'] for p in products]
        self.assertIn(self.product_high.id, product_ids)
        self.assertIn(self.product_med.id, product_ids)
        self.assertNotIn(self.product_zero.id, product_ids)

        # Products must be sorted descending by sales_count
        sales_counts = [p['sales_count'] for p in products]
        self.assertEqual(sales_counts, sorted(sales_counts, reverse=True))
        self.assertEqual(products[0]['id'], self.product_high.id)

        # Categories must include categories of selling products
        category_ids = [c['id'] for c in categories]
        self.assertIn(self.category_a.id, category_ids)
        self.assertIn(self.category_b.id, category_ids)

    def test_multi_category_association(self):
        """Test that a product associated with multiple categories appears in both."""
        mock_request = MagicMock()
        mock_request.env = self.env(context=dict(self.env.context, website_id=self.website.id))
        mock_request.website = self.website

        with patch('odoo.addons.top_selling_products_in_category.controllers.top_selling_products_in_category.request', mock_request):
            products, categories, _website_id = self.controller.products_categories()

        high_product_data = next((p for p in products if p['id'] == self.product_high.id), None)
        self.assertIsNotNone(high_product_data)
        # Verify both category IDs are in public_categ_ids
        self.assertIn(self.category_a.id, high_product_data['public_categ_ids'])
        self.assertIn(self.category_b.id, high_product_data['public_categ_ids'])
