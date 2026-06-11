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

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPaymentDetailsInvoiceReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPaymentDetailsInvoiceReport, cls).setUpClass()
        # Set up a company, a partner, a product, and an account
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
            'taxes_id': False,
        })
        cls.account_revenue = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_id', '=', cls.company.id)
        ], limit=1)

        # Ensure we have a journal for payment
        cls.bank_journal = cls.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', cls.company.id)
        ], limit=1)
        if not cls.bank_journal:
            cls.bank_journal = cls.env['account.journal'].create({
                'name': 'Bank',
                'code': 'BNK',
                'type': 'bank',
                'company_id': cls.company.id,
            })

    def test_payment_details_field(self):
        """Test if the payment_details field is properly set and readable."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'payment_details': True,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
                'account_id': self.account_revenue.id,
            })],
        })
        self.assertTrue(invoice.payment_details, "Payment details should be True")
        invoice.payment_details = False
        self.assertFalse(invoice.payment_details, "Payment details should be False")

    def test_invoice_payment_report(self):
        """Test the report rendering with payment details enabled."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'payment_details': True,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
                'account_id': self.account_revenue.id,
            })],
        })
        invoice.action_post()
        
        # Register a payment to transition payment_state
        payment_register = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=invoice.ids,
        ).create({
            'amount': 100.0,
            'journal_id': self.bank_journal.id,
            'payment_date': '2025-01-01',
        })
        payment = payment_register._create_payments()
        
        self.assertEqual(invoice.payment_state, 'paid', "Invoice should be paid")
        
        # Test report rendering
        report = self.env.ref('account.report_invoice_with_payments')
        report_html, _ = report._render_qweb_html(invoice.ids)
        
        # Check if the payment details string is in the report HTML
        self.assertIn(b'Payment Details', report_html, "Payment Details string should be present in the report HTML when payment_details is True and print_with_payments is True")

        # Set payment_details to False and verify it's absent
        invoice.payment_details = False
        report_html_without_details, _ = report._render_qweb_html(invoice.ids)
        self.assertNotIn(b'Payment Details', report_html_without_details, "Payment Details string should NOT be present in the report HTML when payment_details is False")
