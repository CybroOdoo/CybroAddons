# -*- coding: utf-8 -*-
from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestAccountMove(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bank_journal = cls.company_data['default_journal_bank']
        cls.cash_journal = cls.company_data['default_journal_cash']
        cls.general_journal = cls.company_data['default_journal_misc']
        cls.invoice_for_listing = cls.create_customer_invoice('Listing Invoice', 125.0)
        cls.vendor_bill = cls.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': cls.partner_a.id,
            'invoice_date': '2026-05-11',
            'invoice_line_ids': [
                Command.create({
                    'name': 'Vendor Bill Line',
                    'quantity': 1.0,
                    'price_unit': 70.0,
                    'product_id': cls.product_a.id,
                    'tax_ids': [],
                }),
            ],
        })

    @classmethod
    def create_customer_invoice(cls, line_name, amount):
        return cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner_a.id,
            'invoice_date': '2026-05-11',
            'invoice_line_ids': [
                Command.create({
                    'name': line_name,
                    'quantity': 1.0,
                    'price_unit': amount,
                    'product_id': cls.product_a.id,
                    'tax_ids': [],
                }),
            ],
        })

    def test_get_invoices_returns_customer_invoice_values(self):
        invoices = self.env['account.move'].get_invoices()
        invoice_entry = next(
            invoice for invoice in invoices
            if invoice['invoice_id'] == self.invoice_for_listing.id
        )

        self.assertEqual(invoice_entry['payment_reference'], self.invoice_for_listing.payment_reference)
        self.assertEqual(invoice_entry['partner_id'], self.invoice_for_listing.partner_id.name)
        self.assertEqual(invoice_entry['amount_total'], self.invoice_for_listing.amount_total)
        self.assertEqual(invoice_entry['amount_residual'], self.invoice_for_listing.amount_residual)
        self.assertEqual(invoice_entry['state'], self.invoice_for_listing.state)
        self.assertEqual(invoice_entry['payment_state'], self.invoice_for_listing.payment_state)
        self.assertNotIn(self.vendor_bill.id, [invoice['invoice_id'] for invoice in invoices])

    def test_post_invoice_posts_draft_invoice(self):
        invoice = self.create_customer_invoice('Draft Invoice', 80.0)

        self.env['account.move'].post_invoice(invoice.id)

        self.assertEqual(invoice.state, 'posted')

    def test_register_payment_creates_payment_for_invoice(self):
        invoice = self.create_customer_invoice('Invoice To Pay', 95.0)
        invoice.action_post()
        existing_payment_ids = self.env['account.payment'].search([
            ('partner_id', '=', invoice.partner_id.id),
            ('amount', '=', invoice.amount_total),
            ('payment_type', '=', 'inbound'),
            ('partner_type', '=', 'customer'),
        ]).ids

        self.env['account.move'].register_payment(invoice.id)

        new_payments = self.env['account.payment'].search([
            ('id', 'not in', existing_payment_ids),
            ('partner_id', '=', invoice.partner_id.id),
            ('amount', '=', invoice.amount_total),
            ('payment_type', '=', 'inbound'),
            ('partner_type', '=', 'customer'),
        ])
        self.assertTrue(new_payments)
        self.assertEqual(new_payments.state, 'posted')
        self.assertEqual(invoice.amount_residual, 0.0)
