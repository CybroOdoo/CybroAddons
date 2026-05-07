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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError

class TestProductTags(TransactionCase):

    def setUp(self):
        super(TestProductTags, self).setUp()
        # Create some tags
        self.tag_1 = self.env['product.tag'].create({'name': 'Tag 1'})
        self.tag_2 = self.env['product.tag'].create({'name': 'Tag 2'})
        
        # Create a product to use with the wizard
        self.product_template = self.env['product.template'].create({
            'name': 'Test Product Template',
            'list_price': 100.0,
        })
        self.product_product = self.env['product.product'].create({
            'name': 'Test Product Variant',
            'lst_price': 150.0,
        })

    def test_01_default_tags_on_product_create(self):
        """Test default tags from config parameters are applied on creation."""
        # Set default tags in config parameters
        self.env['ir.config_parameter'].sudo().set_param(
            'odoo_product_tags.product_tag_ids', [self.tag_1.id, self.tag_2.id])
        
        # Create a new product template
        new_template = self.env['product.template'].create({
            'name': 'New Product Template With Default Tags',
        })
        self.assertIn(self.tag_1, new_template.product_tag_ids, "Tag 1 should be applied by default")
        self.assertIn(self.tag_2, new_template.product_tag_ids, "Tag 2 should be applied by default")

        # Create a new product variant
        new_product = self.env['product.product'].create({
            'name': 'New Product Variant With Default Tags',
        })
        self.assertIn(self.tag_1, new_product.product_tag_ids, "Tag 1 should be applied by default on variant")
        self.assertIn(self.tag_2, new_product.product_tag_ids, "Tag 2 should be applied by default on variant")

    def test_02_wizard_apply_tags(self):
        """Test the wizard to apply tags to products and templates."""
        # Test applying to templates
        wizard_template = self.env['product.multiple.tag'].with_context(
            active_ids=[self.product_template.id],
            active_model='product.template'
        ).create({
            'product_tag_ids': [(6, 0, [self.tag_1.id])],
            'is_product_template': True,
        })
        wizard_template.action_apply_template_tags()
        self.assertIn(self.tag_1, self.product_template.product_tag_ids, "Tag 1 should be applied to template via wizard")

        # Test applying to variants
        wizard_product = self.env['product.multiple.tag'].with_context(
            active_ids=[self.product_product.id],
            active_model='product.product'
        ).create({
            'product_tag_ids': [(6, 0, [self.tag_2.id])],
            'is_product': True,
        })
        wizard_product.action_apply_product_tags()
        self.assertIn(self.tag_2, self.product_product.product_tag_ids, "Tag 2 should be applied to product via wizard")

    def test_03_res_config_settings(self):
        """Test res.config.settings saving default tags."""
        config = self.env['res.config.settings'].create({
            'product_tag_ids': [(6, 0, [self.tag_1.id, self.tag_2.id])],
        })
        config.set_values()
        
        param_value = self.env['ir.config_parameter'].sudo().get_param('odoo_product_tags.product_tag_ids')
        self.assertEqual(eval(param_value), [self.tag_1.id, self.tag_2.id], "Config parameter should match saved tags")
        
        # Test get_values
        config_new = self.env['res.config.settings'].create({})
        values = config_new.get_values()
        # values['product_tag_ids'] is (6, 0, [ids])
        self.assertEqual(values['product_tag_ids'][0][2], [self.tag_1.id, self.tag_2.id], "get_values should return correct tags")
