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
from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestInvoiceMiniDashboard(AccountTestInvoicingCommon):
    """Check the figures returned for the mini dashboard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

    def _create_move(self, move_type, price, post=True, currency=None,
                     company=None):
        company = company or self.company
        move = self.env['account.move'].with_company(company).create({
            'move_type': move_type,
            'partner_id': self.partner_a.id,
            'invoice_date': fields.Date.from_string('2026-06-01'),
            'currency_id': (currency or company.currency_id).id,
            'invoice_line_ids': [Command.create({
                'name': 'Dashboard line',
                'quantity': 1,
                'price_unit': price,
                'tax_ids': [],
            })],
        })
        if post:
            move.action_post()
        return move

    def _register_payment(self, move, amount=None):
        wizard = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=move.ids)
        values = {'amount': amount} if amount else {}
        wizard.create(values)._create_payments()

    def _delta(self, method, action):
        """Return the change of every dashboard value caused by `action`."""
        before = getattr(self.env['account.move'], method)()
        action()
        after = getattr(self.env['account.move'], method)()
        return {key: after[key] - before[key] for key in before
                if key != 'company_currency_symbol'}

    def test_result_keys_and_symbol(self):
        data = self.env['account.move'].retrieve_out_invoice_dashboard()
        self.assertEqual(
            data['company_currency_symbol'], self.company.currency_id.symbol)
        for key in ('draft', 'posted', 'cancelled', 'paid', 'not_paid',
                    'paid_amount', 'not_paid_amount', 'lost_amount',
                    'expected_amount'):
            self.assertIn(key, data)

    def test_customer_invoice_states(self):
        def action():
            self._create_move('out_invoice', 100, post=False)
            self._create_move('out_invoice', 200)
            cancelled = self._create_move('out_invoice', 50)
            cancelled.button_draft()
            cancelled.button_cancel()

        delta = self._delta('retrieve_out_invoice_dashboard', action)
        self.assertEqual(delta['draft'], 1)
        self.assertEqual(delta['posted'], 1)
        self.assertEqual(delta['cancelled'], 1)
        self.assertEqual(delta['not_paid'], 1)
        self.assertEqual(delta['not_paid_amount'], 200)
        self.assertEqual(delta['expected_amount'], 200)
        self.assertEqual(delta['lost_amount'], 50)

    def test_customer_invoice_paid(self):
        def action():
            invoice = self._create_move('out_invoice', 300)
            self._register_payment(invoice)

        delta = self._delta('retrieve_out_invoice_dashboard', action)
        self.assertEqual(delta['posted'], 1)
        self.assertEqual(delta['not_paid'], 0)
        self.assertEqual(delta['not_paid_amount'], 0)
        self.assertEqual(delta['expected_amount'], 0)
        # "paid" is based on payment_state, like the "Paid" filter.
        paid_moves = self.env['account.move'].search_count([
            ('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),
            ('payment_state', '=', 'paid'),
            ('company_id', '=', self.company.id)])
        data = self.env['account.move'].retrieve_out_invoice_dashboard()
        self.assertEqual(data['paid'], paid_moves)

    def test_partial_payment_counts_remaining_amount(self):
        def action():
            invoice = self._create_move('out_invoice', 400)
            self._register_payment(invoice, amount=100)

        delta = self._delta('retrieve_out_invoice_dashboard', action)
        self.assertEqual(delta['posted'], 1)
        self.assertEqual(delta['not_paid'], 0)
        self.assertEqual(delta['expected_amount'], 300)

    def test_vendor_bill_amounts_are_positive(self):
        def action():
            self._create_move('in_invoice', 100, post=False)
            self._create_move('in_invoice', 250)

        delta = self._delta('retrieve_in_invoice_dashboard', action)
        self.assertEqual(delta['draft'], 1)
        self.assertEqual(delta['posted'], 1)
        self.assertEqual(delta['not_paid'], 1)
        self.assertEqual(delta['not_paid_amount'], 250)
        self.assertEqual(delta['expected_amount'], 250)

    def test_vendor_bill_cancelled_and_paid(self):
        def action():
            bill = self._create_move('in_invoice', 80)
            bill.button_draft()
            bill.button_cancel()
            paid = self._create_move('in_invoice', 120)
            self._register_payment(paid)

        delta = self._delta('retrieve_in_invoice_dashboard', action)
        self.assertEqual(delta['cancelled'], 1)
        self.assertEqual(delta['lost_amount'], 80)
        self.assertEqual(delta['posted'], 1)
        self.assertEqual(delta['not_paid'], 0)

    def test_amounts_use_company_currency(self):
        foreign = self.env.ref('base.EUR')
        if foreign == self.company.currency_id:
            foreign = self.env.ref('base.USD')
        foreign.active = True
        self.env['res.currency.rate'].create({
            'name': '2026-01-01',
            'currency_id': foreign.id,
            'rate': 2.0,
            'company_id': self.company.id,
        })
        invoices = []

        def action():
            invoices.append(
                self._create_move('out_invoice', 200, currency=foreign))

        delta = self._delta('retrieve_out_invoice_dashboard', action)
        expected = abs(invoices[0].amount_total_signed)
        self.assertEqual(delta['not_paid_amount'], expected)
        self.assertNotEqual(delta['not_paid_amount'], 200)

    def test_other_company_is_ignored(self):
        other_company = self.setup_other_company()['company']

        def action():
            self._create_move('out_invoice', 500, company=other_company)

        delta = self._delta('retrieve_out_invoice_dashboard', action)
        self.assertTrue(all(value == 0 for value in delta.values()))
