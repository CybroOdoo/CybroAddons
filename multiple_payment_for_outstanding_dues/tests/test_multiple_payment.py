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
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestMultiplePayment(AccountTestInvoicingCommon):
    """Tests for the due amount, due statements and multiple payment flow"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({'name': 'Due Customer'})
        cls.invoice_1 = cls.init_invoice(
            'out_invoice', partner=cls.customer, amounts=[100.0],
            post=True)
        cls.invoice_2 = cls.init_invoice(
            'out_invoice', partner=cls.customer, amounts=[250.0],
            post=True)

    def test_due_amount(self):
        """Only posted, unpaid customer invoices are counted as due"""
        self.init_invoice('out_invoice', partner=self.customer,
                          amounts=[999.0])
        self.init_invoice('in_invoice', partner=self.customer,
                          amounts=[999.0], post=True)
        expected = (self.invoice_1.amount_residual_signed
                    + self.invoice_2.amount_residual_signed)
        self.assertAlmostEqual(self.customer.due_amount, expected)

    def test_due_amount_foreign_currency(self):
        """Invoices in another currency are counted in the company currency"""
        other_currency = self.setup_other_currency('EUR')
        partner = self.env['res.partner'].create({'name': 'Foreign Customer'})
        # The rate on the default invoice date (2019-01-01) is 2.0
        invoice = self.init_invoice('out_invoice', partner=partner,
                                    amounts=[200.0], post=True,
                                    currency=other_currency)
        self.assertAlmostEqual(invoice.amount_residual, 200.0)
        self.assertEqual(partner.currency_id, self.env.company.currency_id)
        self.assertAlmostEqual(partner.due_amount, 100.0)

    def test_due_amount_no_invoices(self):
        """A customer without invoices has no due amount"""
        partner = self.env['res.partner'].create({'name': 'No Dues'})
        self.assertEqual(partner.due_amount, 0.0)

    def test_action_view_due_statements(self):
        """The due statements action lists the lines of unpaid invoices"""
        action = self.customer.action_view_due_statements()
        self.assertEqual(action['res_model'], 'account.move.line')
        self.assertFalse(action['context']['create'])
        self.assertTrue(action['context']['search_default_group_by_invoices'])
        self.assertEqual(
            action['views'][0][0],
            self.env.ref('multiple_payment_for_outstanding_dues.'
                         'account_move_line_view_tree').id)
        lines = self.env['account.move.line'].search(action['domain'])
        self.assertEqual(lines.move_id, self.invoice_1 | self.invoice_2)

    def test_register_payment_from_lines(self):
        """Paying the selected lines pays their invoices"""
        action = self.env['account.move.line'].search(
            self.customer.action_view_due_statements()['domain']
        ).action_register_payment()
        self.assertEqual(action['res_model'], 'account.payment.register')
        context = action['context']
        self.assertEqual(context['active_model'], 'account.move')
        self.assertCountEqual(context['active_ids'],
                              (self.invoice_1 | self.invoice_2).ids)
        self.assertTrue(context['dont_redirect_to_payments'])
        wizard = self.env['account.payment.register'].with_context(
            **context).create({'group_payment': True})
        wizard.action_create_payments()
        self.assertTrue(all(
            state in ('paid', 'in_payment') for state in
            (self.invoice_1 | self.invoice_2).mapped('payment_state')))
        self.customer.invalidate_recordset(['due_amount'])
        self.assertEqual(self.customer.due_amount, 0.0)
        due_lines = self.env['account.move.line'].search(
            self.customer.action_view_due_statements()['domain'])
        self.assertFalse(due_lines)

    def test_register_payment_extra_context(self):
        """Extra context passed to the action is kept"""
        action = self.invoice_1.line_ids.action_register_payment(
            ctx={'default_group_payment': True})
        self.assertTrue(action['context']['default_group_payment'])
        self.assertEqual(action['context']['active_ids'], self.invoice_1.ids)

    def test_pay_now_from_invoice(self):
        """The 'Pay Now' button pays a single invoice"""
        action = self.invoice_1.action_register_payment()
        self.assertEqual(action['context']['active_ids'], self.invoice_1.ids)
        self.env['account.payment.register'].with_context(
            **action['context']).create({}).action_create_payments()
        self.assertIn(self.invoice_1.payment_state, ('paid', 'in_payment'))
        self.customer.invalidate_recordset(['due_amount'])
        self.assertAlmostEqual(self.customer.due_amount,
                               self.invoice_2.amount_residual_signed)

    def test_pay_now_draft_invoice(self):
        """A draft invoice cannot be paid"""
        draft = self.init_invoice('out_invoice', partner=self.customer,
                                  amounts=[50.0])
        with self.assertRaises(UserError):
            draft.action_register_payment()

    def test_server_action(self):
        """The 'Pay Due Payment(s)' action opens the payment wizard"""
        server_action = self.env.ref(
            'multiple_payment_for_outstanding_dues.'
            'action_account_invoice_from_list')
        lines = self.invoice_1.invoice_line_ids
        result = server_action.with_context(
            active_model='account.move.line', active_ids=lines.ids,
            active_id=lines[:1].id).run()
        self.assertEqual(result['res_model'], 'account.payment.register')
        self.assertEqual(result['context']['active_ids'], self.invoice_1.ids)
