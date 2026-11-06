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
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

# Characters removed from the generated SEO content
STRIP_CHARS = "<>(),'/"


@tagged('post_install', '-at_install')
class TestWebsiteSeoKit(TransactionCase):
    """Tests for the Website SEO Kit module"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        attribute_model = cls.env['website.seo.attributes']
        cls.attr_product_name = attribute_model.create({
            'name': 'Test Product Name Attr',
            'product': 'name',
            'models': 'product',
        })
        cls.attr_product_desc = attribute_model.create({
            'name': 'Test Product Description Attr',
            'product': 'description_sale',
            'models': 'product',
        })
        cls.attr_category_name = attribute_model.create({
            'name': 'Test Category Name Attr',
            'category': 'name',
            'models': 'product_category',
        })
        cls.attr_category_desc = attribute_model.create({
            'name': 'Test Category Description Attr',
            'category': 'category_description',
            'models': 'product_category',
        })
        cls.product = cls.env['product.template'].create({
            'name': "Product (1), 'Test' <p>Name</p>",
            'description_sale': 'Test Description sale',
        })
        cls.category = cls.env['product.public.category'].create({
            'name': "Category (1), 'Test' <p>Name</p>",
            'is_auto_seo': True,
            'category_description': 'Test Category Desc',
        })

    def test_seo_attribute_unique_name(self):
        """The name of website.seo.attributes must be unique."""
        self.env['website.seo.attributes'].create({
            'name': 'exact duplicate name',
            'product': 'name',
            'models': 'product',
        })
        with self.assertRaises(ValidationError):
            self.env['website.seo.attributes'].create({
                'name': 'exact duplicate name',
                'product': 'name',
                'models': 'product',
            })

    def test_seo_attribute_unique_name_case_insensitive(self):
        """The uniqueness check ignores the case of the name."""
        self.env['website.seo.attributes'].create({
            'name': 'Case Duplicate',
            'product': 'name',
            'models': 'product',
        })
        with self.assertRaises(ValidationError):
            self.env['website.seo.attributes'].create({
                'name': 'case duplicate',
                'product': 'name',
                'models': 'product',
            })

    def test_onchange_model_name(self):
        """Changing model_name updates meta_ids accordingly."""
        seo_gen = self.env['seo.generate'].create({
            'model_name': 'product',
            'meta_title_ids': [(6, 0, [self.attr_product_name.id])],
            'meta_description_ids': [(6, 0, [self.attr_product_desc.id])],
        })
        seo_gen._onchange_model_name()

        self.assertFalse(seo_gen.meta_title_ids)
        self.assertFalse(seo_gen.meta_description_ids)
        self.assertIn(self.attr_product_name, seo_gen.meta_ids)
        self.assertIn(self.attr_product_desc, seo_gen.meta_ids)
        self.assertNotIn(self.attr_category_name, seo_gen.meta_ids)

        seo_gen.model_name = 'product_category'
        seo_gen._onchange_model_name()
        self.assertIn(self.attr_category_name, seo_gen.meta_ids)
        self.assertIn(self.attr_category_desc, seo_gen.meta_ids)
        self.assertNotIn(self.attr_product_name, seo_gen.meta_ids)

    def test_action_save_seo_info_product(self):
        """action_save_seo_info generates the SEO of the products."""
        seo_gen = self.env['seo.generate'].create({
            'model_name': 'product',
            'meta_title_ids': [(6, 0, [self.attr_product_name.id])],
            'meta_description_ids': [(6, 0, [self.attr_product_desc.id])],
            'attribute_separator': '-',
        })
        res = seo_gen.action_save_seo_info()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(seo_gen.state, 'activated')

        self.product.invalidate_recordset()
        translation = str.maketrans('', '', STRIP_CHARS)
        expected_title = self.product.name.translate(translation)
        expected_desc = self.product.description_sale.translate(translation)

        self.assertEqual(expected_title, 'Product 1 Test pNamep')
        self.assertEqual(self.product.website_meta_title, expected_title)
        self.assertEqual(self.product.website_meta_keywords,
                         self.product.name)
        self.assertEqual(self.product.website_meta_description, expected_desc)

    def test_action_save_seo_info_multiple_attributes(self):
        """Multiple attributes are joined with the separator."""
        attr_code = self.env['website.seo.attributes'].create({
            'name': 'Test Product Reference Attr',
            'product': 'default_code',
            'models': 'product',
        })
        self.product.default_code = 'REF01'
        seo_gen = self.env['seo.generate'].create({
            'model_name': 'product',
            'meta_title_ids': [
                (6, 0, [self.attr_product_name.id, attr_code.id])],
            'meta_description_ids': [(6, 0, [self.attr_product_desc.id])],
            'attribute_separator': '-',
        })
        seo_gen.action_save_seo_info()
        self.product.invalidate_recordset()
        self.assertEqual(self.product.website_meta_title,
                         'Product 1 Test pNamep-REF01')

    def test_action_save_seo_info_category(self):
        """action_save_seo_info generates the SEO of the categories."""
        seo_gen = self.env['seo.generate'].create({
            'model_name': 'product_category',
            'meta_title_ids': [(6, 0, [self.attr_category_name.id])],
            'meta_description_ids': [(6, 0, [self.attr_category_desc.id])],
            'attribute_separator': '-',
        })
        res = seo_gen.action_save_seo_info()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(seo_gen.state, 'activated')

        self.category.invalidate_recordset()
        translation = str.maketrans('', '', STRIP_CHARS)
        expected_title = self.category.name.translate(translation)
        expected_desc = self.category.category_description.translate(
            translation)

        self.assertEqual(expected_title, 'Category 1 Test pNamep')
        self.assertEqual(self.category.website_meta_title, expected_title)
        self.assertEqual(self.category.website_meta_keywords,
                         self.category.name)
        self.assertEqual(self.category.website_meta_description, expected_desc)

    def test_action_deactivate_seo(self):
        """action_deactivate_seo sets the record as deactivated."""
        seo_gen = self.env['seo.generate'].create({
            'model_name': 'product',
            'meta_title_ids': [(6, 0, [self.attr_product_name.id])],
            'meta_description_ids': [(6, 0, [self.attr_product_desc.id])],
            'state': 'activated',
        })
        seo_gen.action_deactivate_seo()
        self.assertEqual(seo_gen.state, 'deactivated')
