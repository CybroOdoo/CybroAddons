# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from .common import AccountKitCommon


@tagged('post_install', '-at_install')
class TestBulkPayment(AccountKitCommon):

    def _method_line(self, direction='outbound'):
        field = ('outbound_payment_method_line_ids' if direction == 'outbound'
                 else 'inbound_payment_method_line_ids')
        return self.bank_journal[field].filtered(lambda l: l.code == 'manual')[:1]

    def _payment(self, amount=100.0, direction='outbound'):
        ptype = 'supplier' if direction == 'outbound' else 'customer'
        return self.env['account.payment'].create({
            'payment_type': direction,
            'partner_type': ptype,
            'partner_id': self.partner_a.id,
            'amount': amount,
            'journal_id': self.bank_journal.id,
            'payment_method_line_id': self._method_line(direction).id,
        })

    def test_add_to_bulk_creates_batch(self):
        """The 'Add to Bulk Payment' action groups compatible payments."""
        p1, p2 = self._payment(100.0), self._payment(50.0)
        action = (p1 | p2).action_add_to_bulk_payment()
        batch = self.env['account.bulk.payment'].browse(action['res_id'])
        self.assertEqual(batch.payment_ids, p1 | p2)
        self.assertEqual(batch.payment_count, 2)
        self.assertAlmostEqual(batch.amount_total, 150.0, 2)
        self.assertTrue(batch.name.startswith('BULK/'))

    def test_validate_posts_and_marks_sent(self):
        """Validating the batch posts its draft payments and closes it."""
        p1 = self._payment(100.0)
        batch = self.env['account.bulk.payment'].create({
            'journal_id': self.bank_journal.id, 'batch_type': 'outbound'})
        p1.bulk_payment_id = batch
        batch.action_validate()
        self.assertEqual(batch.state, 'sent')
        self.assertNotEqual(p1.state, 'draft', "Draft payment is posted")
        self.assertTrue(p1.is_sent)

    def test_consistency_constraint(self):
        """Payments of a different type can't be added to the batch."""
        batch = self.env['account.bulk.payment'].create({
            'journal_id': self.bank_journal.id, 'batch_type': 'outbound'})
        inbound = self._payment(10.0, direction='inbound')
        with self.assertRaises(ValidationError):
            batch.payment_ids = inbound  # inbound into an outbound batch

    def test_print_returns_report_action(self):
        """The print button returns the batch-slip report action."""
        p1 = self._payment(100.0)
        batch = self.env['account.bulk.payment'].create({
            'journal_id': self.bank_journal.id, 'batch_type': 'outbound'})
        p1.bulk_payment_id = batch
        action = batch.action_print()
        # In v19 this is the report action, or the letterhead-config wizard when
        # no external report layout is set yet — either way a valid action dict.
        self.assertIsInstance(action, dict)
        self.assertTrue(action.get('type'))
