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
class TestImportVendorPricelist(TransactionCase):

    def setUp(self):
        super().setUp()
        if 'product.supplierinfo' not in self.env:
            self.skipTest("Product app is not installed")
        self.Wizard = self.env['import.vendor.pricelist']
        self.Vendor = self.env['res.partner'].create({'name': 'Vendor Pricelist Partner'})
        self.ProductTemplate = self.env['product.template'].create({'name': 'Vendor Pricelist Product'})

    def test_action_import_vendor_pricelist_csv(self):
        """Test importing vendor pricelist from CSV"""
        csv_content = (
            "Vendor,Product Template,Quantity,Price,Delivery Lead Time\n"
            "Vendor Pricelist Partner,Vendor Pricelist Product,10,15.5,5"
        )
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'company_id': self.env.company.id
        })
        wizard.action_import_vendor_pricelist()

        supplierinfo = self.env['product.supplierinfo'].search([
            ('partner_id', '=', self.Vendor.id),
            ('product_tmpl_id', '=', self.ProductTemplate.id)
        ])
        self.assertTrue(supplierinfo, "Supplierinfo record should be created")
        self.assertEqual(supplierinfo.price, 15.5)
        self.assertEqual(supplierinfo.min_qty, 10.0)
