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
class TestImportProductTemplate(TransactionCase):

    def setUp(self):
        super().setUp()
        if 'product.template' not in self.env:
            self.skipTest("Product app is not installed")
        self.Wizard = self.env['import.product.template']

    def test_action_import_product_template_csv(self):
        """Test importing product template from CSV"""
        csv_content = (
            "Name,Product Type,Internal Reference,Sales Price,Cost\n"
            "Widget Alpha,consu,WIDG-001,49.99,25.00\n"
            "Gadget Beta,service,GADG-002,99.99,50.00"
        )
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'method': 'create_product',
            'import_product_by': 'name'
        })
        wizard.action_import_product_template()

        product = self.env['product.template'].search([('name', '=', 'Widget Alpha')])
        self.assertTrue(product, "Product template should be created")
        self.assertEqual(product.default_code, 'WIDG-001')
        self.assertEqual(product.type, 'consu')
