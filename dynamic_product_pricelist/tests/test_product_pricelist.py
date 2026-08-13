# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fansa Jabeen A (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.tests import common
from odoo.tests.common import tagged


@tagged('post_install', '-at_install')
class TestProductDynamicPricelist(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a category
        cls.category = cls.env['product.category'].create({
            'name': 'Test Category',
        })

        # Create templates
        cls.product_template_1 = cls.env['product.template'].create({
            'name': 'Test Product Template 1',
            'list_price': 100.0,
            'categ_id': cls.category.id,
        })

        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Test Product Template 2',
            'list_price': 150.0,
            'categ_id': cls.category.id,
        })

        # Get variants
        cls.product_variant_1 = cls.product_template_1.product_variant_id
        cls.product_variant_2 = cls.product_template_2.product_variant_id

    def test_01_global_pricelist(self):
        """ Test dynamic pricelist applied globally. """
        pricelist = self.env['product.pricelist'].create({
            'name': 'Global Pricelist',
            'is_show_product_pricelist': True,
            'item_ids': [(0, 0, {
                'applied_on': '3_global',
                'compute_price': 'fixed',
                'fixed_price': 80.0,
            })]
        })

        # Check if the custom field has been created on product.template model
        field_name = 'x_temp_%sGlobal_Pricelist' % pricelist.id
        field = self.env['ir.model.fields'].search([
            ('name', '=', field_name),
            ('model', '=', 'product.template')
        ])
        self.assertTrue(field, "Dynamic field for global pricelist was not created on product.template")

        # Check standard view inheritance
        view_name = 'product.dynamic.fields.Global_Pricelist'
        view = self.env['ir.ui.view'].search([
            ('name', '=', view_name),
            ('model', '=', 'product.template')
        ])
        self.assertTrue(view, "Dynamic view was not created for global pricelist")
        self.assertTrue(view.active, "Dynamic view should be active")

        # Verify the prices are updated (using fresh browse to ensure registry/fields setup is loaded)
        template_1 = self.env['product.template'].browse(self.product_template_1.id)
        template_2 = self.env['product.template'].browse(self.product_template_2.id)
        self.assertEqual(template_1[field_name], 80.0)
        self.assertEqual(template_2[field_name], 80.0)

    def test_02_category_pricelist(self):
        """ Test dynamic pricelist applied on a product category. """
        pricelist = self.env['product.pricelist'].create({
            'name': 'Category Pricelist',
            'is_show_product_pricelist': True,
            'item_ids': [(0, 0, {
                'applied_on': '2_product_category',
                'categ_id': self.category.id,
                'compute_price': 'fixed',
                'fixed_price': 90.0,
            })]
        })

        field_name = 'x_temp_%sCategory_Pricelist' % pricelist.id
        field = self.env['ir.model.fields'].search([
            ('name', '=', field_name),
            ('model', '=', 'product.template')
        ])
        self.assertTrue(field, "Dynamic field for category pricelist was not created on product.template")

        # Verify the prices are updated for products in that category
        template_1 = self.env['product.template'].browse(self.product_template_1.id)
        template_2 = self.env['product.template'].browse(self.product_template_2.id)
        self.assertEqual(template_1[field_name], 90.0)
        self.assertEqual(template_2[field_name], 90.0)

    def test_03_variant_pricelist(self):
        """ Test dynamic pricelist applied on a product variant. """
        pricelist = self.env['product.pricelist'].create({
            'name': 'Variant Pricelist',
            'is_show_product_pricelist': True,
            'item_ids': [(0, 0, {
                'applied_on': '0_product_variant',
                'product_id': self.product_variant_1.id,
                'compute_price': 'fixed',
                'fixed_price': 70.0,
            })]
        })

        field_name = 'x_variant_%sVariant_Pricelist' % pricelist.id
        field = self.env['ir.model.fields'].search([
            ('name', '=', field_name),
            ('model', '=', 'product.product')
        ])
        self.assertTrue(field, "Dynamic field for variant pricelist was not created on product.product")

        # Check standard view inheritance
        view_name = 'product.dynamic.fields.Variant_Pricelist'
        view = self.env['ir.ui.view'].search([
            ('name', '=', view_name),
            ('model', '=', 'product.product')
        ])
        self.assertTrue(view, "Dynamic view was not created for variant pricelist")
        self.assertTrue(view.active, "Dynamic view should be active")

        # Verify the price is updated only for the targeted variant
        variant_1 = self.env['product.product'].browse(self.product_variant_1.id)
        variant_2 = self.env['product.product'].browse(self.product_variant_2.id)
        self.assertEqual(variant_1[field_name], 70.0)
        self.assertNotEqual(variant_2[field_name], 70.0)

    def test_04_product_template_pricelist(self):
        """ Test dynamic pricelist applied on a specific product template (default case). """
        pricelist = self.env['product.pricelist'].create({
            'name': 'Template Pricelist',
            'is_show_product_pricelist': True,
            'item_ids': [(0, 0, {
                'applied_on': '1_product',
                'product_tmpl_id': self.product_template_1.id,
                'compute_price': 'fixed',
                'fixed_price': 60.0,
            })]
        })

        field_name = 'x_temp_%sTemplate_Pricelist' % pricelist.id
        field = self.env['ir.model.fields'].search([
            ('name', '=', field_name),
            ('model', '=', 'product.template')
        ])
        self.assertTrue(field, "Dynamic field for template pricelist was not created on product.template")

        # Verify the price is updated only for targeted template
        template_1 = self.env['product.template'].browse(self.product_template_1.id)
        template_2 = self.env['product.template'].browse(self.product_template_2.id)
        self.assertEqual(template_1[field_name], 60.0)
        self.assertNotEqual(template_2[field_name], 60.0)

    def test_05_pricelist_write_condition(self):
        """ Test that check_pricelist_condition triggers on write. """
        pricelist = self.env['product.pricelist'].create({
            'name': 'Write Pricelist',
            'is_show_product_pricelist': False,
            'item_ids': [(0, 0, {
                'applied_on': '3_global',
                'compute_price': 'fixed',
                'fixed_price': 50.0,
            })]
        })

        field_name = 'x_temp_%sWrite_Pricelist' % pricelist.id
        field = self.env['ir.model.fields'].search([
            ('name', '=', field_name),
            ('model', '=', 'product.template')
        ])
        self.assertFalse(field, "Dynamic field should not be created if is_show_product_pricelist is False")

        # Toggle is_show_product_pricelist to True
        pricelist.write({'is_show_product_pricelist': True})

        field = self.env['ir.model.fields'].search([
            ('name', '=', field_name),
            ('model', '=', 'product.template')
        ])
        self.assertTrue(field, "Dynamic field should be created after toggling is_show_product_pricelist to True")

    def test_06_pricelist_unlink(self):
        """ Test that unlink removes the generated custom fields and deactivates views. """
        pricelist = self.env['product.pricelist'].create({
            'name': 'Unlink Pricelist',
            'is_show_product_pricelist': True,
            'item_ids': [(0, 0, {
                'applied_on': '3_global',
                'compute_price': 'fixed',
                'fixed_price': 40.0,
            })]
        })

        field_name = 'x_temp_%sUnlink_Pricelist' % pricelist.id
        field = self.env['ir.model.fields'].search([
            ('name', '=', field_name),
            ('model', '=', 'product.template')
        ])
        self.assertTrue(field, "Dynamic field should exist before unlink")

        view_name = 'product.dynamic.fields.Unlink_Pricelist'
        view = self.env['ir.ui.view'].search([
            ('name', '=', view_name),
            ('model', '=', 'product.template')
        ])
        self.assertTrue(view, "Dynamic view should exist before unlink")

        # Unlink the pricelist
        pricelist.unlink()

        # Field should be deleted
        field_after = self.env['ir.model.fields'].search([
            ('name', '=', field_name),
            ('model', '=', 'product.template')
        ])
        self.assertFalse(field_after, "Dynamic field should be deleted after unlink")

        # View should be deactivated (active=False)
        view_after = self.env['ir.ui.view'].search([
            ('name', '=', view_name),
            ('model', '=', 'product.template'),
            ('active', '=', True)
        ])
        self.assertFalse(view_after, "Dynamic view should be deactivated (active=False) after unlink")
