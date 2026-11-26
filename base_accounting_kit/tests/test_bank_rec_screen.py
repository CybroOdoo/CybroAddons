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
from datetime import timedelta

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestBankRecScreen(AccountingKitTestCommon):
    """P2.1-c reconciliation screen, server side: groups, drawer data,
    validation (full, part, difference kept open or booked with a model),
    accept all sure, to check / undo, access rights."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bank = cls.company_data['default_journal_bank']
        cls.fees = cls.env['account.account'].create({'name': 'Kit screen fees', 'code': 'KSFEE',
                                                      'account_type': 'expense'})

    def new_partner(self, name):
        return self.env['res.partner'].create({'name': name})

    def invoice(self, partner, amount):
        return self.init_invoice('out_invoice', partner=partner, amounts=[amount], invoice_date=self.today, post=True)

    def receivable(self, invoice):
        return invoice.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable')

    def statement_line(self, amount, label, partner=None):
        return self.env['account.bank.statement.line'].create({
            'journal_id': self.bank.id, 'date': self.today, 'payment_ref': label, 'amount': amount,
            'partner_id': partner.id if partner else False})

    def rows(self, **filters):
        data = self.env['account.bank.statement.line'].kit_rec_load(dict({'journal_id': self.bank.id}, **filters))
        return {row['id']: row for row in data['rows']}

    # ------------------------------------------------------------------
    def test_groups(self):
        """Sure match (reference + amount), please confirm (several items
        adding up), needs you (nothing); reconciled lines leave the list
        and appear under Reconciled."""
        sure_partner, many = self.new_partner('Kit Sure'), self.new_partner('Kit Many')
        inv = self.invoice(sure_partner, 300)
        a, b = self.invoice(many, 100), self.invoice(many, 250)
        sure = self.statement_line(inv.amount_total, 'Payment %s' % inv.name)
        confirm = self.statement_line(a.amount_total + b.amount_total, 'Transfer', many)
        needs = self.statement_line(77.77, 'Unknown')
        rows = self.rows()
        self.assertEqual(rows[sure.id]['group'], 'sure')
        self.assertEqual(rows[sure.id]['proposal'], inv.name)
        self.assertEqual(rows[sure.id]['partner_found'], sure_partner.display_name)
        self.assertEqual(rows[confirm.id]['group'], 'confirm')
        self.assertEqual(rows[needs.id]['group'], 'needs')
        drawer = confirm.kit_rec_line()
        self.assertEqual(set(drawer['selected']), set((self.receivable(a) | self.receivable(b)).ids))
        self.assertEqual(len(drawer['combinations']), 1)
        count = self.env['account.bank.statement.line'].kit_rec_accept_sure([sure.id, confirm.id, needs.id])
        self.assertEqual(count, 1)
        self.assertNotIn(sure.id, self.rows())
        self.assertEqual(self.rows(status='done')[sure.id]['group'], 'done')
        self.assertIn(needs.id, self.rows(search='unkno'))
        self.assertIn(needs.id, self.rows(search='77.77'))
        self.assertNotIn(needs.id, self.rows(search='zzz'))

    def test_validate_items(self):
        """Ticked items with amounts: all of it, part of an item with the
        rest on suspense, or the difference kept open on the last item."""
        partner = self.new_partner('Kit Validate')
        a, b = self.invoice(partner, 100), self.invoice(partner, 250)
        line = self.statement_line(a.amount_total + b.amount_total, 'Transfer', partner)
        line.kit_rec_validate({'items': [[self.receivable(a).id, None], [self.receivable(b).id, None]]})
        self.assertTrue(line.is_reconciled)
        self.assertEqual((a | b).mapped('payment_state'), ['paid', 'paid'])
        c = self.invoice(partner, 400)
        part = self.statement_line(150, 'Part', partner)
        part.kit_rec_validate({'items': [[self.receivable(c).id, 100]], 'gap': 'suspense'})
        self.assertFalse(part.is_reconciled)
        self.assertAmount(c.amount_residual, c.amount_total - 100)
        d = self.invoice(partner, 500)
        short = self.statement_line(d.amount_total - 20, 'Short', partner)
        short.kit_rec_validate({'items': [[self.receivable(d).id, d.amount_total]], 'gap': 'open'})
        self.assertTrue(short.is_reconciled)
        self.assertAmount(d.amount_residual, 20)
        with self.assertRaises(UserError):
            short.kit_rec_validate({'items': []})

    def test_validate_with_model(self):
        """The difference is booked with the chosen model; a model alone
        books the whole amount."""
        model = self.env['account.reconcile.model'].create({'name': 'Kit screen model', 'line_ids': [
            Command.create({'account_id': self.fees.id, 'amount_type': 'percentage', 'amount_string': '100'})]})
        partner = self.new_partner('Kit Model')
        inv = self.invoice(partner, 100)
        line = self.statement_line(inv.amount_total - 2, 'Pay', partner)
        line.kit_rec_validate({'items': [[self.receivable(inv).id, None]], 'gap': 'model', 'model_id': model.id})
        self.assertTrue(line.is_reconciled)
        self.assertEqual(inv.payment_state, 'paid')
        self.assertAmount(line.move_id.line_ids.filtered(lambda l: l.account_id == self.fees).balance, 2)
        alone = self.statement_line(-30, 'Something')
        alone.kit_rec_validate({'gap': 'model', 'model_id': model.id})
        self.assertTrue(alone.is_reconciled)
        self.assertEqual(alone.kit_rec_line()['row']['group'], 'done')

    def test_check_and_undo(self):
        """To check moves the line to the To check list (core review
        state); Undo puts a reconciled line back to reconcile."""
        partner = self.new_partner('Kit Undo')
        inv = self.invoice(partner, 90)
        line = self.statement_line(inv.amount_total, 'Pay', partner)
        line.kit_rec_validate({'items': [[self.receivable(inv).id, None]], 'to_check': True})
        self.assertEqual(self.rows(status='check')[line.id]['group'], 'check')
        line.kit_rec_set_check(False)
        self.assertEqual(self.rows(status='done')[line.id]['group'], 'done')
        line.kit_rec_undo()
        self.assertIn(line.id, self.rows())
        self.assertNotEqual(inv.payment_state, 'paid')

    def test_rights_and_stale_items(self):
        """A user without accounting rights cannot validate; an item that
        is no longer open is refused."""
        partner = self.new_partner('Kit Rights')
        inv = self.invoice(partner, 60)
        line = self.statement_line(inv.amount_total, 'Pay', partner)
        user = new_test_user(self.env, login='kit_rec_noacc', groups='base.group_user')
        with self.assertRaises(AccessError):
            line.with_user(user).kit_rec_validate({'items': [[self.receivable(inv).id, None]]})
        other = self.statement_line(inv.amount_total, 'Other', partner)
        other.kit_rec_validate({'items': [[self.receivable(inv).id, None]]})
        with self.assertRaises(UserError):
            line.kit_rec_validate({'items': [[self.receivable(inv).id, None]]})

    # ------------------------------------------------------------------
    def epd_invoice(self, partner, amount):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': partner.id, 'invoice_date': self.today,
            'invoice_payment_term_id': self.env.ref('account.account_payment_term_30days_early_discount').id,
            'invoice_line_ids': [Command.create({'name': 'Lamp', 'quantity': 1, 'price_unit': amount,
                                                 'tax_ids': False})]})
        invoice.action_post()
        return invoice

    def test_early_payment_discount(self):
        """Paid in time with core's early payment discount: a sure match,
        the invoice is paid and the discount goes to the company's cash
        discount loss account (as core's Register Payment); also from the
        drawer ('discount'). Paid after the discount date it is no match."""
        partner = self.new_partner('Kit EPD')
        invoice = self.epd_invoice(partner, 750)
        term = self.receivable(invoice)
        self.assertAmount(term.discount_amount_currency, 735)
        line = self.statement_line(735, 'Transfer', partner)
        self.assertEqual(self.rows()[line.id]['group'], 'sure')
        self.assertIn('Early payment discount', self.rows()[line.id]['reasons'])
        drawer = line.kit_rec_line()
        self.assertEqual(drawer['gap'], 'discount')
        self.assertAmount(drawer['suggestions'][0]['discounted'], 735)
        self.env['account.bank.statement.line'].kit_rec_accept_sure([line.id])
        self.assertTrue(line.is_reconciled)
        self.assertEqual(invoice.payment_state, 'paid')
        loss = self.company.account_journal_early_pay_discount_loss_account_id
        self.assertAmount(sum(line.move_id.line_ids.filtered(lambda l: l.account_id == loss).mapped('balance')), 15)
        other = self.epd_invoice(partner, 750)
        manual = self.statement_line(735, 'Pay', partner)
        manual.kit_rec_validate({'items': [[self.receivable(other).id, None]], 'gap': 'discount'})
        self.assertEqual(other.payment_state, 'paid')
        late_invoice = self.epd_invoice(self.new_partner('Kit EPD late'), 750)
        late = self.env['account.bank.statement.line'].create({
            'journal_id': self.bank.id, 'date': self.receivable(late_invoice).discount_date + timedelta(days=1),
            'payment_ref': 'Late', 'amount': 735, 'partner_id': late_invoice.partner_id.id})
        self.assertFalse([s for s in late._suggestions() if s['same_amount']])

    def test_preview_matches_posted_entry(self):
        """The preview shows the entry Validate posts, and saves nothing."""
        partner = self.new_partner('Kit Preview')
        inv = self.invoice(partner, 100)
        line = self.statement_line(inv.amount_total - 5, 'Pay', partner)
        selection = {'items': [[self.receivable(inv).id, None]], 'gap': 'open'}
        before = line.move_id.line_ids.ids
        preview = line.kit_rec_preview(selection)
        self.assertEqual(line.move_id.line_ids.ids, before)
        line.kit_rec_validate(selection)
        posted = sorted((l.debit, l.credit) for l in line.move_id.line_ids)
        shown = sorted((round(l['debit'], 2), round(l['credit'], 2)) for l in preview['lines'])
        self.assertEqual(shown, posted)

    def test_book_to_accounts(self):
        """Book to account: several lines, taxes and analytic; an empty
        amount takes the rest."""
        plan = self.env['account.analytic.plan'].create({'name': 'Kit screen plan'})
        analytic = self.env['account.analytic.account'].create({'name': 'Kit Shop', 'plan_id': plan.id})
        other = self.env['account.account'].create({'name': 'Kit screen other', 'code': 'KSOTH',
                                                    'account_type': 'expense'})
        line = self.statement_line(-215, 'Card')
        line.kit_rec_validate({'writeoffs': [
            {'account_id': self.fees.id, 'amount': 115, 'tax_ids': self.tax_purchase_a.ids,
             'analytic_distribution': {str(analytic.id): 100}, 'label': 'Fee'},
            {'account_id': other.id, 'amount': 0, 'label': 'Rest'}]})
        self.assertTrue(line.is_reconciled)
        items = line.move_id.line_ids
        fee = items.filtered(lambda l: l.account_id == self.fees)
        self.assertAmount(fee.balance, 100)
        self.assertEqual(fee.analytic_distribution, {str(analytic.id): 100})
        self.assertEqual(len(items.filtered('tax_repartition_line_id')), 1)
        self.assertAmount(items.filtered(lambda l: l.account_id == other).balance, 100)

    def test_search_and_partner(self):
        """Search finds open items by number or amount; the drawer can
        suggest for another partner."""
        partner = self.new_partner('Kit Search')
        inv = self.invoice(partner, 432.10)
        line = self.statement_line(10, 'Something')
        found = line.kit_rec_search(inv.name)['items']
        self.assertEqual([item['id'] for item in found], self.receivable(inv).ids)
        self.assertIn(self.receivable(inv).id, [i['id'] for i in line.kit_rec_search('%.2f' % inv.amount_total)['items']])
        drawer = line.kit_rec_line(partner.id)
        self.assertEqual(drawer['partner']['id'], partner.id)
        self.assertIn(self.receivable(inv).id, [s['id'] for s in drawer['suggestions']])
