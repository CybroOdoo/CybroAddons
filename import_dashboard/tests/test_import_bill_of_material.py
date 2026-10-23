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
class TestImportBillOfMaterial(TransactionCase):

    def setUp(self):
        super().setUp()
        if 'mrp.bom' not in self.env:
            self.skipTest("Manufacturing app is not installed")
        self.Wizard = self.env['import.bill.of.material']
        self.Product = self.env['product.product'].create({'name': 'Finished Good'})
        self.Component = self.env['product.product'].create({'name': 'Raw Material'})

    def test_action_import_bom_csv(self):
        """Test importing BOM from CSV"""
        csv_content = "Product,Component,Quantity\nFinished Good,Raw Material,5"
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        })
        wizard.action_import_bom()
        bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.Product.product_tmpl_id.id)])
        self.assertTrue(bom, "BOM should have been created")

    def test_import_bom_creates_missing_products(self):
        """Unknown product and component are created and reported by name"""
        csv_content = "Product,Component,Quantity\nNew Finished Good,New Raw Material,2"
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        })
        result = wizard.action_import_bom()

        product_tmpl = self.env['product.template'].search([('name', '=', 'New Finished Good')])
        self.assertTrue(product_tmpl, "Missing product should have been created")
        bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_tmpl.id)])
        self.assertEqual(bom.bom_line_ids.product_id.name, 'New Raw Material')
        message = result['effect']['message']
        self.assertIn('Product "New Finished Good" was not found', message)
        self.assertIn('Component "New Raw Material" was not found', message)
        self.assertNotIn('name is missing', message)
