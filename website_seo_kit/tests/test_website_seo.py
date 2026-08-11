# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Surya Gayathry TA (odoo@cybrosys.com)
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
############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestWebsiteSeoKit(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestWebsiteSeoKit, cls).setUpClass()
        
        # Create some SEO attributes
        cls.attr_product_name = cls.env['website.seo.attributes'].create({
            'name': 'Test Product Name Attr',
            'product': 'name',
            'models': 'product'
        })
        cls.attr_product_desc = cls.env['website.seo.attributes'].create({
            'name': 'Test Product Description Attr',
            'product': 'description_sale',
            'models': 'product'
        })
        
        cls.attr_category_name = cls.env['website.seo.attributes'].create({
            'name': 'Test Category Name Attr',
            'category': 'name',
            'models': 'product_category'
        })
        cls.attr_category_desc = cls.env['website.seo.attributes'].create({
            'name': 'Test Category Description Attr',
            'category': 'category_description',
            'models': 'product_category'
        })

        # Create products
        cls.product = cls.env['product.template'].create({
            'name': "Product (1), 'Test' <p>Name</p>",
            'description_sale': 'Test Description sale'
        })

        # Create category
        cls.category = cls.env['product.public.category'].create({
            'name': "Category (1), 'Test' <p>Name</p>",
            'is_auto_seo': True,
            'category_description': 'Test Category Desc'
        })

    def test_seo_attribute_unique_name(self):
        """Test that the name of website.seo.attributes is unique."""
        self.env['website.seo.attributes'].create({
            'name': 'exact duplicate name',
            'product': 'name',
            'models': 'product'
        })
        with self.assertRaises(ValidationError):
            self.env['website.seo.attributes'].create({
                'name': 'exact duplicate name',
                'product': 'name',
                'models': 'product'
            })

    def test_onchange_model_name(self):
        """Test that changing model_name updates meta_ids accordingly."""
        seo_gen = self.env['seo.generate'].create({
            'model_name': 'product',
            'meta_title_ids': [(6, 0, [self.attr_product_name.id])],
            'meta_description_ids': [(6, 0, [self.attr_product_desc.id])]
        })
        seo_gen._onchange_model_name()
        
        # meta_title_ids and meta_description_ids should be False
        self.assertFalse(seo_gen.meta_title_ids)
        self.assertFalse(seo_gen.meta_description_ids)
        
        # meta_ids should contain product models
        self.assertIn(self.attr_product_name.id, seo_gen.meta_ids.ids)
        self.assertIn(self.attr_product_desc.id, seo_gen.meta_ids.ids)
        self.assertNotIn(self.attr_category_name.id, seo_gen.meta_ids.ids)

        # change to product_category
        seo_gen.model_name = 'product_category'
        seo_gen._onchange_model_name()
        self.assertIn(self.attr_category_name.id, seo_gen.meta_ids.ids)
        self.assertIn(self.attr_category_desc.id, seo_gen.meta_ids.ids)
        self.assertNotIn(self.attr_product_name.id, seo_gen.meta_ids.ids)

    def test_action_save_seo_info_product(self):
        """Test action_save_seo_info for product."""
        seo_gen = self.env['seo.generate'].create({
            'model_name': 'product',
            'meta_title_ids': [(6, 0, [self.attr_product_name.id])],
            'meta_description_ids': [(6, 0, [self.attr_product_desc.id])],
            'attribute_separator': '-'
        })
        res = seo_gen.action_save_seo_info()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(seo_gen.state, 'activated')
        
        self.product.invalidate_recordset()
        
        expected_title = self.product.name.translate({ord(i): None for i in "<p>(),'</p>"})
        expected_desc = self.product.description_sale.translate({ord(i): None for i in "<p>(),'</p>"})
        
        self.assertEqual(self.product.website_meta_title, expected_title)
        self.assertEqual(self.product.website_meta_keywords, self.product.name)
        self.assertEqual(self.product.website_meta_description, expected_desc)

    def test_action_save_seo_info_category(self):
        """Test action_save_seo_info for product category."""
        seo_gen = self.env['seo.generate'].create({
            'model_name': 'product_category',
            'meta_title_ids': [(6, 0, [self.attr_category_name.id])],
            'meta_description_ids': [(6, 0, [self.attr_category_desc.id])],
            'attribute_separator': '-'
        })
        res = seo_gen.action_save_seo_info()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(seo_gen.state, 'activated')

        self.category.invalidate_recordset()
        expected_title = self.category.name.translate({ord(i): None for i in "<p>(),'</p>"})
        expected_desc = self.category.category_description.translate({ord(i): None for i in "<p>(),'</p>"})

        self.assertEqual(self.category.website_meta_title, expected_title)
        self.assertEqual(self.category.website_meta_keywords, self.category.name)
        self.assertEqual(self.category.website_meta_description, expected_desc)
        
    def test_action_deactivate_seo(self):
        """Test action_deactivate_seo."""
        seo_gen = self.env['seo.generate'].create({
            'model_name': 'product',
            'meta_title_ids': [(6, 0, [self.attr_product_name.id])],
            'meta_description_ids': [(6, 0, [self.attr_product_desc.id])],
            'state': 'activated'
        })
        seo_gen.action_deactivate_seo()
        self.assertEqual(seo_gen.state, 'deactivated')
