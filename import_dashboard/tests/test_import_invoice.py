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
class TestImportInvoice(TransactionCase):

    def setUp(self):
        super().setUp()
        if 'account.move' not in self.env or 'product.product' not in self.env:
            self.skipTest("Invoicing app is not installed")
        self.Wizard = self.env['import.invoice']
        self.Partner = self.env['res.partner'].create({'name': 'Customer A'})
        self.Product = self.env['product.product'].create({'name': 'Service'})

    def test_action_import_invoice_csv(self):
        """Test importing invoice from CSV"""
        csv_content = "Partner,Number,Product,Quantity,Price\nCustomer A,INV/2026/001,Service,1,100"
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'type': 'out_invoice',
            'import_product_by': 'name'
        })

        wizard.action_import_invoice()

        invoice = self.env['account.move'].search([('name', '=', 'INV/2026/001')])
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.partner_id, self.Partner)
        self.assertEqual(invoice.invoice_line_ids[0].product_id, self.Product)

    def test_auto_post_multi_line_invoice(self):
        """Auto-post posts a multi-line invoice once, after all its lines are added"""
        csv_content = (
            "Partner,Number,Product,Quantity,Price\n"
            "Customer A,INV/2026/002,Service,1,100\n"
            "Customer A,INV/2026/002,Service,2,50"
        )
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'type': 'out_invoice',
            'import_product_by': 'name',
            'auto_post': True,
        })

        wizard.action_import_invoice()

        invoice = self.env['account.move'].search([('name', '=', 'INV/2026/002')])
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.state, 'posted')
        self.assertEqual(len(invoice.invoice_line_ids), 2)
