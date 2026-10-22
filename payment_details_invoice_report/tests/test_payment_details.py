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
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestPaymentDetailsInvoiceReport(AccountTestInvoicingCommon):
    """Tests for the payment details toggle, the payment details
    collection on account.move and the invoice report."""

    REPORT_NAME = 'account.report_invoice_with_payments'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice = cls.init_invoice(
            'out_invoice', amounts=[1000.0], post=True)
        cls.bill = cls.init_invoice(
            'in_invoice', amounts=[500.0], post=True)

    @classmethod
    def _register_payment(cls, move, amount=None):
        """Register a payment for the given posted move and return it."""
        values = {}
        if amount is not None:
            values['amount'] = amount
        return cls.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=move.ids,
        ).create(values)._create_payments()

    def _render_report(self, move):
        report = self.env['ir.actions.report']
        content, _report_type = report._render_qweb_html(
            self.REPORT_NAME, move.ids)
        return content.decode()

    def test_toggle_default_is_false(self):
        """The payment details toggle is disabled by default."""
        self.assertFalse(self.invoice.is_payment_details)

    def test_toggle_can_be_enabled(self):
        """The payment details toggle can be switched on and off."""
        self.invoice.is_payment_details = True
        self.assertTrue(self.invoice.is_payment_details)
        self.invoice.is_payment_details = False
        self.assertFalse(self.invoice.is_payment_details)

    def test_toggle_in_form_view(self):
        """The toggle is added to the account.move form view."""
        view = self.env['account.move'].get_view(view_type='form')
        self.assertIn('is_payment_details', view['arch'])

    def test_no_payment_returns_empty_list(self):
        """An unpaid invoice has no payment details."""
        self.assertEqual(self.invoice.payment_state, 'not_paid')
        self.assertEqual(self.invoice.get_payment_details(), [])

    def test_partial_payment_details(self):
        """A partially paid invoice lists the payment with its values."""
        amount = self.invoice.amount_total / 2
        payment = self._register_payment(self.invoice, amount)
        self.assertEqual(self.invoice.payment_state, 'partial')

        details = self.invoice.get_payment_details()
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0]['ref'], payment.move_id.name)
        self.assertEqual(details[0]['date'], payment.date)
        self.assertEqual(details[0]['journal_name'], payment.journal_id.name)
        self.assertAlmostEqual(details[0]['amount_company_currency'], amount)

    def test_full_payment_details(self):
        """A fully paid invoice lists the payment for the whole total."""
        payment = self._register_payment(self.invoice)
        self.assertIn(self.invoice.payment_state, ('paid', 'in_payment'))

        details = self.invoice.get_payment_details()
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0]['ref'], payment.move_id.name)
        self.assertAlmostEqual(
            details[0]['amount_company_currency'], self.invoice.amount_total)

    def test_multiple_payment_details(self):
        """Every payment registered on the invoice is listed."""
        amount = self.invoice.amount_total / 4
        payments = (self._register_payment(self.invoice, amount)
                    + self._register_payment(self.invoice, amount))

        details = self.invoice.get_payment_details()
        self.assertEqual(len(details), 2)
        self.assertEqual(
            sorted(detail['ref'] for detail in details),
            sorted(payments.move_id.mapped('name')))
        self.assertAlmostEqual(
            sum(detail['amount_company_currency'] for detail in details),
            amount * 2)

    def test_vendor_bill_payment_details(self):
        """Payment details are also available for vendor bills."""
        amount = self.bill.amount_total / 2
        payment = self._register_payment(self.bill, amount)

        details = self.bill.get_payment_details()
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0]['ref'], payment.move_id.name)
        self.assertAlmostEqual(details[0]['amount_company_currency'], amount)

    def test_report_with_payment_details_enabled(self):
        """The report shows the status and the payment details table."""
        self.invoice.is_payment_details = True
        payment = self._register_payment(
            self.invoice, self.invoice.amount_total / 2)

        html = self._render_report(self.invoice)
        self.assertIn('Invoice Status:', html)
        self.assertIn('payment_details_table', html)
        self.assertIn(payment.move_id.name, html)

    def test_report_with_payment_details_disabled(self):
        """The report hides the payment details table when disabled."""
        self.invoice.is_payment_details = False
        self._register_payment(self.invoice, self.invoice.amount_total / 2)

        html = self._render_report(self.invoice)
        self.assertIn('Invoice Status:', html)
        self.assertNotIn('payment_details_table', html)
