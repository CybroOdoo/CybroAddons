# -*- coding: utf-8 -*-
from datetime import date
from odoo.tests import tagged
from .common import AccountKitCommon


@tagged('post_install', '-at_install')
class TestPaymentPDC(AccountKitCommon):

    def _pdc_line(self, direction='outbound'):
        field = ('outbound_payment_method_line_ids' if direction == 'outbound'
                 else 'inbound_payment_method_line_ids')
        return self.bank_journal[field].filtered(lambda l: l.code == 'pdc')[:1]

    def test_pdc_method_line_created_on_bank_journal(self):
        """The post_init hook links the PDC payment method to bank journals."""
        self.assertTrue(self._pdc_line('outbound'),
                        "Outbound PDC method line must exist on the bank journal")
        self.assertTrue(self._pdc_line('inbound'),
                        "Inbound PDC method line must exist on the bank journal")

    def test_pdc_move_is_post_dated_to_effective_date(self):
        """A PDC payment's journal entry (and maturity) use the effective date,
        not the payment date."""
        pdc_line = self._pdc_line('outbound')
        payment = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': self.partner_a.id,
            'amount': 100.0,
            'date': '2020-01-01',
            'journal_id': self.bank_journal.id,
            'payment_method_line_id': pdc_line.id,
            'effective_date': '2020-03-01',
        })
        payment.action_post()
        self.assertEqual(payment.move_id.date, date(2020, 3, 1),
                         "PDC journal entry must be dated on the effective date")
        self.assertTrue(all(
            l.date_maturity == date(2020, 3, 1) for l in payment.move_id.line_ids),
            "PDC move line maturity must be the effective date")

    def test_non_pdc_payment_keeps_payment_date(self):
        """A normal (non-PDC) payment's move keeps the payment date."""
        manual_line = self.bank_journal.outbound_payment_method_line_ids.filtered(
            lambda l: l.code == 'manual')[:1]
        payment = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': self.partner_a.id,
            'amount': 50.0,
            'date': '2020-01-01',
            'journal_id': self.bank_journal.id,
            'payment_method_line_id': manual_line.id,
        })
        payment.action_post()
        self.assertEqual(payment.move_id.date, date(2020, 1, 1))
