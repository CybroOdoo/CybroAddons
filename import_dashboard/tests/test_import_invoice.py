# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64
from odoo.tests.common import TransactionCase

class TestImportInvoice(TransactionCase):

    def setUp(self):
        super(TestImportInvoice, self).setUp()
        self.Wizard = self.env['import.invoice']
        self.Partner = self.env['res.partner'].create({'name': 'Customer A'})
        self.Product = self.env['product.product'].create({'name': 'Service'})

    def test_action_import_invoice_csv(self):
        """Test importing invoice from CSV"""
        csv_content = "Partner,Number,Product,Quantity,Price\nCustomer A,INV/2026/001,Service,1,100"
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file': base64.b64encode(csv_content.encode('utf-8')),
            'type': 'out_invoice',
            'import_product_by': 'name'
        })
        
        wizard.action_import_invoice()
        
        invoice = self.env['account.move'].search([('name', '=', 'INV/2026/001')])
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.partner_id, self.Partner)
        self.assertEqual(invoice.invoice_line_ids[0].product_id, self.Product)
