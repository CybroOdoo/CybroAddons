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
class TestImportPurchaseOrder(TransactionCase):

    def setUp(self):
        super().setUp()
        if 'purchase.order' not in self.env:
            self.skipTest("Purchase app is not installed")
        self.Wizard = self.env['import.purchase.order']
        self.Vendor = self.env['res.partner'].create({'name': 'Vendor Test Company'})
        self.Product = self.env['product.product'].create({'name': 'Purchase Test Material'})

    def test_action_import_purchase_order_csv(self):
        """Test importing purchase order from CSV"""
        csv_content = (
            "Order Reference,Vendor,Product,Quantity,Unit Price\n"
            "PO/TEST/001,Vendor Test Company,Purchase Test Material,5,20.0"
        )
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'import_product_by': 'name',
            'order_number': 'from_file'
        })
        wizard.action_import_purchase_order()

        po = self.env['purchase.order'].search([('name', '=', 'PO/TEST/001')])
        self.assertTrue(po, "Purchase order should be created")
        self.assertEqual(len(po.order_line), 1)
        self.assertEqual(po.order_line[0].product_id, self.Product)
