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
class TestImportSaleOrder(TransactionCase):

    def setUp(self):
        super().setUp()
        if 'sale.order' not in self.env:
            self.skipTest("Sales app is not installed")
        self.Wizard = self.env['import.sale.order']
        self.Customer = self.env['res.partner'].create({'name': 'Sale Test Customer'})
        self.Product = self.env['product.product'].create({'name': 'Sale Test Product', 'lst_price': 50.0})

    def test_action_import_sale_order_csv(self):
        """Test importing sale order from CSV"""
        csv_content = (
            "Order Reference,Customer,Product,Quantity,Price\n"
            "SO/TEST/001,Sale Test Customer,Sale Test Product,3,50.0"
        )
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'import_product_by': 'name',
            'order_number': 'from_file'
        })
        wizard.action_import_sale_order()

        so = self.env['sale.order'].search([('name', '=', 'SO/TEST/001')])
        self.assertTrue(so, "Sale order should be created")
        self.assertEqual(len(so.order_line), 1)
        self.assertEqual(so.order_line[0].product_id, self.Product)
