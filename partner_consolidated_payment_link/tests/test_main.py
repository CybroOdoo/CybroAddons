# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1). It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included in
#    all copies or substantial portions of the Software.
#
#############################################################################

from odoo.addons.account.tests.common import AccountTestInvoicingHttpCommon
from odoo.tests import tagged
from odoo import Command

@tagged('post_install', '-at_install')
class TestPartnerConsolidatedPaymentLinkController(AccountTestInvoicingHttpCommon):
    
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.partner = cls.env['res.partner'].create({'name': 'Test Controller Partner'})
            
        cls.move = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_line_ids': [Command.create({
                'name': 'Test Line',
                'quantity': 1,
                'price_unit': 100.0,
                'tax_ids': [],
                'account_id': cls.company_data['default_account_revenue'].id,
            })],
        })
        cls.move.action_post()

    def test_create_payment_link(self):
        """Test generating payment link and redirection"""
        self.url_open(f'/payment/balance/{self.partner.id}')
        self.assertTrue(self.move.consolidated_payment_link_ref)

    def test_create_payment_link_no_dues(self):
        """Test payment link generation when there are no dues"""
        self.move.button_draft()
        self.move.button_cancel()
        response = self.url_open(f'/payment/balance/{self.partner.id}')
        self.assertIn(b'All outstanding invoices are settled.', response.content)
