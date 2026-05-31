# -*- coding: utf-8 -*-
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestAccountPayment(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bank_journal = cls.company_data['default_journal_bank']

    def test_create_payment_creates_posted_customer_payment(self):
        existing_payment_ids = self.env['account.payment'].search([
            ('partner_id', '=', self.partner_a.id),
            ('journal_id', '=', self.bank_journal.id),
            ('currency_id', '=', self.company_data['company'].currency_id.id),
            ('amount', '=', 55.0),
            ('payment_type', '=', 'inbound'),
            ('partner_type', '=', 'customer'),
        ]).ids

        self.env['account.payment'].create_payment({
            'journal_id': str(self.bank_journal.id),
            'partner_id': str(self.partner_a.id),
            'currency_id': str(self.company_data['company'].currency_id.id),
            'amount': '55.0',
        })

        new_payment = self.env['account.payment'].search([
            ('id', 'not in', existing_payment_ids),
            ('partner_id', '=', self.partner_a.id),
            ('journal_id', '=', self.bank_journal.id),
            ('currency_id', '=', self.company_data['company'].currency_id.id),
            ('amount', '=', 55.0),
            ('payment_type', '=', 'inbound'),
            ('partner_type', '=', 'customer'),
        ], limit=1)
        self.assertTrue(new_payment)
        self.assertEqual(new_payment.state, 'posted')
