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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):
    """Test cases for product.template model in product_brand_sale module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductBrand = cls.env['product.brand']
        cls.ProductTemplate = cls.env['product.template']

        cls.brand_1 = cls.ProductBrand.create({'name': 'Brand Alpha'})
        cls.brand_2 = cls.ProductBrand.create({'name': 'Brand Beta'})

    def test_01_product_template_brand_assignment(self):
        """Test assigning a brand when creating a product template."""
        product_tmpl = self.ProductTemplate.create({
            'name': 'Branded Desk',
            'brand_id': self.brand_1.id,
        })
        self.assertEqual(product_tmpl.brand_id, self.brand_1)
        self.assertIn(product_tmpl, self.brand_1.member_ids)

        # Check corresponding product variant
        variant = product_tmpl.product_variant_id
        self.assertTrue(variant, "Variant should exist for product template.")
        self.assertEqual(variant.product_tmpl_id.brand_id, self.brand_1)

    def test_02_product_template_without_brand(self):
        """Test creating a product template without a brand."""
        product_tmpl = self.ProductTemplate.create({
            'name': 'Unbranded Chair',
        })
        self.assertFalse(product_tmpl.brand_id)
        self.assertNotIn(product_tmpl, self.brand_1.member_ids)
        self.assertNotIn(product_tmpl, self.brand_2.member_ids)

    def test_03_change_and_clear_brand(self):
        """Test updating and clearing the brand on a product template."""
        product_tmpl = self.ProductTemplate.create({
            'name': 'Dynamic Product',
            'brand_id': self.brand_1.id,
        })
        self.assertEqual(product_tmpl.brand_id, self.brand_1)
        self.assertIn(product_tmpl, self.brand_1.member_ids)

        # Reassign to brand 2
        product_tmpl.write({'brand_id': self.brand_2.id})
        self.assertEqual(product_tmpl.brand_id, self.brand_2)
        self.assertNotIn(product_tmpl, self.brand_1.member_ids)
        self.assertIn(product_tmpl, self.brand_2.member_ids)

        # Clear brand
        product_tmpl.write({'brand_id': False})
        self.assertFalse(product_tmpl.brand_id)
        self.assertNotIn(product_tmpl, self.brand_2.member_ids)

    def test_04_search_by_brand(self):
        """Test searching product templates filtered by brand_id."""
        tmpl_1 = self.ProductTemplate.create({
            'name': 'Alpha Phone',
            'brand_id': self.brand_1.id,
        })
        tmpl_2 = self.ProductTemplate.create({
            'name': 'Beta Laptop',
            'brand_id': self.brand_2.id,
        })
        tmpl_none = self.ProductTemplate.create({
            'name': 'Generic Mouse',
        })

        alpha_products = self.ProductTemplate.search([('brand_id', '=', self.brand_1.id)])
        self.assertIn(tmpl_1, alpha_products)
        self.assertNotIn(tmpl_2, alpha_products)
        self.assertNotIn(tmpl_none, alpha_products)

        beta_products = self.ProductTemplate.search([('brand_id', '=', self.brand_2.id)])
        self.assertIn(tmpl_2, beta_products)
        self.assertNotIn(tmpl_1, beta_products)
        self.assertNotIn(tmpl_none, beta_products)
