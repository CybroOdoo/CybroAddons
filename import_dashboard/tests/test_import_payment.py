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
class TestImportPayment(TransactionCase):

    def setUp(self):
        super().setUp()
        if 'account.payment' not in self.env:
            self.skipTest("Invoicing app is not installed")
        self.Wizard = self.env['import.payment']
        self.Partner = self.env['res.partner'].create({'name': 'Payment Test Partner'})
        self.Journal = self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))], limit=1)

    def test_action_import_payment_csv(self):
        """Test importing payment from CSV"""
        if not self.Journal:
            self.skipTest("No bank or cash journal found")
        csv_content = f"Customer/Vendor,Amount,Date,Payment Type,Journal,Reference,Number\nPayment Test Partner,150.0,2026-06-01,Receive,{self.Journal.name},Ref123,PAY/2026/001"
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        })
        wizard.action_import_payment()

        payment = self.env['account.payment'].search([('name', '=', 'PAY/2026/001')])
        self.assertTrue(payment, "Payment should be created")
        self.assertEqual(payment.amount, 150.0)
        self.assertEqual(payment.partner_id, self.Partner)
