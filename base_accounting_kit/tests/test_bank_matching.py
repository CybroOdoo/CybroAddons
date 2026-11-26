# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import Command
from odoo.tests import tagged
from odoo.tools.safe_eval import safe_eval

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestBankMatching(AccountingKitTestCommon):
    """P2.1-b matching engine: partner detection, ranked suggestions,
    several items adding up, core matching rules with tolerance, "From
    label" amounts, model activity and origin, partial matching, one search
    per partner in a batch."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bank = cls.company_data['default_journal_bank']
        cls.fees = cls.env['account.account'].create({'name': 'Kit match fees', 'code': 'KMFEE',
                                                      'account_type': 'expense'})
        cls.other = cls.env['account.account'].create({'name': 'Kit match other', 'code': 'KMOTH',
                                                       'account_type': 'expense'})

    def new_partner(self, name):
        return self.env['res.partner'].create({'name': name})

    def invoice(self, partner, amount):
        return self.init_invoice('out_invoice', partner=partner, amounts=[amount],
                                 invoice_date=self.today, post=True)

    def receivable(self, invoice):
        return invoice.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')

    def statement_line(self, amount, label, partner=None, **values):
        return self.env['account.bank.statement.line'].create(dict({
            'journal_id': self.bank.id, 'date': self.today, 'payment_ref': label, 'amount': amount,
            'partner_id': partner.id if partner else False}, **values))

    # ------------------------------------------------------------------
    def test_partner_from_bank_account(self):
        """The owner of the bank account number is found (spaces ignored),
        set on the line, and its open invoice of that amount is matched."""
        partner = self.new_partner('Kit IBAN Customer')
        self.env['res.partner.bank'].create({'partner_id': partner.id, 'account_number': 'BE68 5390 0754 7034'})
        invoice = self.invoice(partner, 430)
        line = self.statement_line(invoice.amount_total, 'Transfer', account_number='BE68539007547034')
        line._auto_reconcile()
        self.assertEqual(line.partner_id, partner)
        self.assertTrue(line.is_reconciled)
        self.assertEqual(invoice.payment_state, 'paid')

    def test_partner_from_name_and_mapping(self):
        """Exact partner name (one partner only), else a partner mapping
        reconcile model whose label condition matches."""
        partner = self.new_partner('Kit Name Customer')
        line = self.statement_line(10, 'x', partner_name='kit name customer')
        self.assertEqual(line._detect_partner(), partner)
        self.new_partner('Kit Twin')
        self.new_partner('Kit Twin')
        self.assertFalse(self.statement_line(10, 'x', partner_name='Kit Twin')._detect_partner())
        mapped = self.new_partner('Kit Mapped Vendor')
        model = self.env['account.reconcile.model'].create({
            'name': 'Kit mapping', 'match_label': 'contains', 'match_label_param': 'ACME',
            'line_ids': [Command.create({'partner_id': mapped.id, 'amount_type': 'percentage',
                                         'amount_string': '100'})]})
        self.assertEqual(model.mapped_partner_id, mapped)
        self.assertEqual(self.statement_line(-10, 'ACME services')._detect_partner(), mapped)

    def test_suggestions_ranked(self):
        """The invoice named in the label with the same amount comes first,
        with its reasons; other open items of the partner follow."""
        partner = self.new_partner('Kit Rank Customer')
        first = self.invoice(partner, 100)
        named = self.invoice(partner, 200)
        line = self.statement_line(named.amount_total, 'Payment %s' % named.name, partner)
        suggestions = line._suggestions()
        self.assertEqual(suggestions[0]['lines'], self.receivable(named))
        self.assertEqual(suggestions[0]['score'], 95)
        self.assertEqual(len(suggestions[0]['reasons']), 3)
        self.assertTrue(suggestions[0]['sure'])
        self.assertIn(self.receivable(first), [s['lines'] for s in suggestions])

    def test_several_items(self):
        """Items that add up to the amount are suggested but not booked;
        when the label names all of them they are reconciled."""
        partner = self.new_partner('Kit Many Customer')
        a, b = self.invoice(partner, 100), self.invoice(partner, 250)
        self.invoice(partner, 400)
        total = a.amount_total + b.amount_total
        line = self.statement_line(total, 'Monthly transfer', partner)
        combination = [s for s in line._suggestions() if len(s['lines']) > 1]
        self.assertEqual(combination[0]['lines'], self.receivable(a) | self.receivable(b))
        self.assertFalse(combination[0]['sure'])
        line._auto_reconcile()
        self.assertFalse(line.is_reconciled)
        named = self.statement_line(total, 'Paying %s and %s' % (a.name, b.name))
        named._auto_reconcile()
        self.assertTrue(named.is_reconciled)
        self.assertEqual(named.partner_id, partner)
        self.assertEqual((a | b).mapped('payment_state'), ['paid', 'paid'])

    def test_matching_rule_tolerance(self):
        """A core matching rule takes the partner's invoices oldest first;
        a gap within its tolerance goes to its counterpart account; a rule
        without counterpart leaves the invoice partly open."""
        rule = self.env['account.reconcile.model'].create({
            'name': 'Kit rule', 'rule_type': 'matching_rule', 'payment_tolerance': 2,
            'payment_tolerance_type': 'percentage',
            'line_ids': [Command.create({'account_id': self.fees.id, 'amount_type': 'percentage',
                                         'amount_string': '100'})]})
        self.assertEqual(rule.trigger, 'auto_reconcile')
        partner = self.new_partner('Kit Rule Customer')
        old, new = self.invoice(partner, 100), self.invoice(partner, 300)
        line = self.statement_line(old.amount_total - 1, 'Transfer', partner)
        line._auto_reconcile()
        self.assertTrue(line.is_reconciled)
        self.assertEqual(old.payment_state, 'paid')
        writeoff = line.move_id.line_ids.filtered(lambda l: l.account_id == self.fees)
        self.assertAmount(writeoff.balance, 1)
        self.assertEqual(writeoff.reconcile_model_id, rule)
        too_far = self.statement_line(new.amount_total - 50, 'Transfer', partner)
        too_far._auto_reconcile()
        self.assertFalse(too_far.is_reconciled)
        rule.line_ids = [Command.clear()]
        short = self.statement_line(new.amount_total - 3, 'Transfer', partner)
        short._auto_reconcile()
        self.assertTrue(short.is_reconciled)
        self.assertEqual(new.payment_state, 'partial')
        self.assertAmount(new.amount_residual, 3)

    def test_amount_from_label(self):
        """"From label" model lines read the amount with their regex."""
        model = self.env['account.reconcile.model'].create({'name': 'Kit regex', 'line_ids': [
            Command.create({'account_id': self.fees.id, 'amount_type': 'regex', 'amount_string': r'FEE: ([\d,.]+)'}),
            Command.create({'account_id': self.other.id, 'amount_type': 'percentage', 'amount_string': '100'})]})
        line = self.statement_line(-1010, 'Transfer FEE: 10,00 EUR')
        line.action_apply_reconcile_model(model.id)
        items = line.move_id.line_ids
        self.assertAmount(items.filtered(lambda l: l.account_id == self.fees).balance, 10)
        self.assertAmount(items.filtered(lambda l: l.account_id == self.other).balance, 1000)
        self.assertTrue(line.is_reconciled)
        for label, pattern, expected in (('BRT: 3358,07 C', r'BRT: ([\d,]+)', 3358.07),
                                         ('total 1,000.50', r'total ([\d,.]+)', 1000.5),
                                         ('total 1,000', r'total ([\d,.]+)', 1000.0),
                                         ('01870912 0009065 00115', r'\s+0*(\d+?)(\d{2})(?=\s)', 90.65)):
            self.assertEqual(self.statement_line(1, label)._amount_from_label(pattern), expected, label)

    def test_model_activity_and_origin(self):
        """Applying a model schedules its next activity and marks the lines
        with it, so the model's smart button lists the entry."""
        model = self.env['account.reconcile.model'].create({
            'name': 'Kit todo', 'next_activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'line_ids': [Command.create({'account_id': self.fees.id, 'amount_type': 'percentage',
                                         'amount_string': '100'})]})
        line = self.statement_line(-25, 'Card fee')
        line.action_apply_reconcile_model(model.id)
        self.assertEqual(line.move_id.activity_ids.activity_type_id, model.next_activity_type_id)
        self.assertEqual(line.move_id.line_ids.filtered(lambda l: l.account_id == self.fees).reconcile_model_id, model)
        self.assertIn(line.move_id.id, safe_eval(str(model.action_reconcile_stat()['domain']))[0][2])

    def test_partial_match(self):
        """Part of an invoice: the invoice keeps the rest open and the rest
        of the bank amount stays on suspense."""
        partner = self.new_partner('Kit Partial Customer')
        invoice = self.invoice(partner, 100)
        line = self.statement_line(invoice.amount_total, 'Part', partner)
        line._reconcile_items([(self.receivable(invoice), 40)])
        self.assertEqual(invoice.payment_state, 'partial')
        self.assertAmount(invoice.amount_residual, invoice.amount_total - 40)
        self.assertFalse(line.is_reconciled)
        suspense = line.move_id.line_ids.filtered(lambda l: l.account_id == self.bank.suspense_account_id)
        self.assertAmount(-suspense.balance, invoice.amount_total - 40)

    def test_batch_searches_once(self):
        """In a batch, open items are searched once per partner."""
        partner = self.new_partner('Kit Batch Customer')
        invoices = [self.invoice(partner, amount) for amount in (11, 22, 33)]
        lines = [self.statement_line(inv.amount_total, 'Batch', partner) for inv in invoices]
        cache = {}
        searches = []
        Line = type(lines[0])
        original = Line._open_items

        def counted(record, partner, cache):
            key = ('items', record.company_id.id, partner.id)
            if key not in cache:
                searches.append(key)
            return original(record, partner, cache)
        Line._open_items = counted
        try:
            for line in lines:
                line._get_reconcile_proposal(cache)
        finally:
            Line._open_items = original
        self.assertEqual(len(searches), 1)
