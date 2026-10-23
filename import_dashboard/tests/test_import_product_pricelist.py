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
import base64
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestImportProductPricelist(TransactionCase):

    def setUp(self):
        super().setUp()
        if 'product.pricelist' not in self.env:
            self.skipTest("Product app is not installed")
        self.Wizard = self.env['import.product.pricelist']
        self.Product = self.env['product.product'].create({'name': 'Pricelist Item Test'})

    def test_action_import_product_pricelist_csv(self):
        """Test importing product pricelist from CSV"""
        csv_content = (
            "Pricelist Name,Applied On,Product,Min Quantity,Price,Start Date,End Date\n"
            "Test Pricelist 2026,Product,Pricelist Item Test,1,25.0,2026-01-01,2026-12-31"
        )
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'import_product_by': 'name',
            'product_pricelist_setting': 'basic'
        })
        wizard.action_import_product_pricelist()

        pricelist = self.env['product.pricelist'].search([('name', '=', 'Test Pricelist 2026')])
        self.assertTrue(pricelist, "Pricelist should be created")

    def test_import_advanced_percentage_by_product_name(self):
        """Advanced rules: percentage discount applied on a product matched by name"""
        csv_content = (
            "Name,Product,Discount%\n"
            "Advanced Pricelist 2026,Pricelist Item Test,15"
        )
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'import_product_by': 'name',
            'product_pricelist_setting': 'advanced',
            'compute_price': 'percentage',
            'applied_on': '1_product',
        })
        wizard.action_import_product_pricelist()

        pricelist = self.env['product.pricelist'].search([('name', '=', 'Advanced Pricelist 2026')])
        self.assertEqual(len(pricelist), 1)
        rule = pricelist.item_ids
        self.assertEqual(len(rule), 1)
        self.assertEqual(rule.compute_price, 'discount')
        self.assertEqual(rule.price_discount, 15)
        self.assertEqual(rule.product_tmpl_id, self.Product.product_tmpl_id)

    def _import_advanced_variant_rule(self, csv_content):
        """Run an advanced percentage import applied on product variants"""
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'import_product_by': 'name',
            'product_pricelist_setting': 'advanced',
            'compute_price': 'percentage',
            'applied_on': '0_product_variant',
        })
        return wizard.action_import_product_pricelist()

    def _create_multi_variant_template(self):
        """Create a template with Red and Blue variants"""
        attribute = self.env['product.attribute'].create({
            'name': 'Pricelist Test Color',
            'value_ids': [(0, 0, {'name': 'Red'}), (0, 0, {'name': 'Blue'})],
        })
        return self.env['product.template'].create({
            'name': 'Pricelist Variant Test',
            'attribute_line_ids': [(0, 0, {
                'attribute_id': attribute.id,
                'value_ids': [(6, 0, attribute.value_ids.ids)],
            })],
        })

    def test_import_advanced_variant_by_product_name(self):
        """Advanced rules on a product variant matched by name"""
        self._import_advanced_variant_rule(
            "Name,Product,Discount%\n"
            "Variant Pricelist 2026,Pricelist Item Test,10")

        pricelist = self.env['product.pricelist'].search([('name', '=', 'Variant Pricelist 2026')])
        rule = pricelist.item_ids
        self.assertEqual(len(rule), 1)
        self.assertEqual(rule.applied_on, '0_product_variant')
        self.assertEqual(rule.product_id, self.Product)
        self.assertEqual(rule.price_discount, 10)

    def test_import_advanced_variant_by_variant_values(self):
        """Variant Values select the right variant when the name matches several"""
        template = self._create_multi_variant_template()
        self._import_advanced_variant_rule(
            "Name,Product,Variant Values,Discount%\n"
            "Variant Values Pricelist 2026,Pricelist Variant Test,Pricelist Test Color: Blue,5")

        pricelist = self.env['product.pricelist'].search([('name', '=', 'Variant Values Pricelist 2026')])
        blue = template.product_variant_ids.filtered(
            lambda v: v.product_template_variant_value_ids.name == 'Blue')
        self.assertEqual(pricelist.item_ids.product_id, blue)

    def test_import_advanced_variant_unmatched_values(self):
        """Variant Values matching no variant skip the row instead of creating a rule"""
        self._create_multi_variant_template()
        result = self._import_advanced_variant_rule(
            "Name,Product,Variant Values,Discount%\n"
            "Unmatched Variant Pricelist 2026,Pricelist Variant Test,Pricelist Test Color: Green,5")

        self.assertEqual(result.get('res_model'), 'import.message')
        message = self.env['import.message'].browse(result['res_id']).message
        self.assertIn('Pricelist Test Color: Green', message)
        pricelist = self.env['product.pricelist'].search([('name', '=', 'Unmatched Variant Pricelist 2026')])
        self.assertFalse(pricelist.item_ids)

    def test_import_advanced_variant_missing_product(self):
        """A row without a product is reported instead of creating a rule"""
        result = self._import_advanced_variant_rule(
            "Name,Product,Discount%\n"
            "Missing Variant Pricelist 2026,,10")

        self.assertEqual(result.get('res_model'), 'import.message')
        pricelist = self.env['product.pricelist'].search([('name', '=', 'Missing Variant Pricelist 2026')])
        self.assertFalse(pricelist.item_ids)
