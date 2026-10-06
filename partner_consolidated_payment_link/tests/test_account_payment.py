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

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo import Command

@tagged('post_install', '-at_install')
class TestAccountPayment(AccountTestInvoicingCommon):
    
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.move = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'consolidated_payment_link_ref': 'test_consolidated_ref',
            'invoice_line_ids': [Command.create({
                'name': 'Test Line',
                'quantity': 1,
                'price_unit': 100.0,
                'tax_ids': [],
                'account_id': cls.company_data['default_account_revenue'].id,
            })],
        })
        cls.move.action_post()
        
        cls.provider = cls.env['payment.provider'].create({
            'name': 'Test Provider',
            'state': 'test',
        })
        cls.payment_method = cls.env['payment.method'].search([], limit=1)
        if not cls.payment_method:
            cls.payment_method = cls.env['payment.method'].create({
                'name': 'Test Method',
                'code': 'test_method',
            })
            
        cls.transaction = cls.env['payment.transaction'].create({
            'amount': 100.0,
            'currency_id': cls.env.company.currency_id.id,
            'provider_id': cls.provider.id,
            'payment_method_id': cls.payment_method.id,
            'reference': 'test_consolidated_ref',
            'partner_id': cls.partner.id,
        })
        
        cls.payment = cls.env['account.payment'].create({
            'partner_id': cls.partner.id,
            'amount': 100.0,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'journal_id': cls.company_data['default_journal_bank'].id,
            'payment_transaction_id': cls.transaction.id,
        })

    def test_action_post(self):
        """Test if the payment action_post links transaction and matched_payment_ids correctly"""
        self.payment.action_post()
        self.assertIn(self.move, self.transaction.invoice_ids)
        self.assertIn(self.payment, self.move.matched_payment_ids)
