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
class TestOpenItems(AccountingKitTestCommon):
    """P2.1-d Open Items: partners with debits and credits, suggestions,
    matching with core reconcile (partial, write-off with tax or model,
    early payment discount), lock dates, the journal items Reconcile action,
    access rights."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.receivable = cls.company_data['default_account_receivable']
        cls.bank_account = cls.company_data['default_journal_bank'].default_account_id
        cls.misc = cls.company_data['default_journal_misc']
        cls.fees = cls.env['account.account'].create({'name': 'Kit open fees', 'code': 'KOFEE',
                                                      'account_type': 'expense'})
        cls.Items = cls.env['account.move.line']

    def new_partner(self, name):
        return self.env['res.partner'].create({'name': name})

    def invoice(self, partner, amount, move_type='out_invoice', term=None):
        vals = {'move_type': move_type, 'partner_id': partner.id, 'invoice_date': self.today,
                'invoice_line_ids': [Command.create({'name': 'x', 'quantity': 1, 'price_unit': amount,
                                                     'tax_ids': False})]}
        if term:
            vals['invoice_payment_term_id'] = term.id
        move = self.env['account.move'].create(vals)
        move.action_post()
        return move

    def term_line(self, move):
        return move.line_ids.filtered(lambda l: l.account_id == self.receivable)

    def payment(self, partner, amount, ref='Transfer', day=None):
        """A customer payment booked as an entry: bank / receivable."""
        move = self.kit_entry(day or self.today, [(self.bank_account, amount, 0),
                                                  (self.receivable, 0, amount, partner)])
        move.ref = ref
        return self.term_line(move)

    def rows(self, **filters):
        return {row['id']: row for row in self.Items.kit_open_load(filters)['rows']}

    def key(self, partner):
        return '%s-%s' % (partner.id, self.receivable.id)

    def selection(self, partner, lines, **values):
        return dict({'account_id': self.receivable.id, 'partner_id': partner.id, 'items': lines.ids,
                     'journal_id': self.misc.id, 'date': str(self.today)}, **values)

    # ------------------------------------------------------------------
    def test_groups_and_accept_sure(self):
        """Invoice and payment naming it: sure, reconciled by Accept all
        sure; the only invoice of a payment's amount, without reference:
        please confirm; partners with one side only are not listed."""
        sure, confirm, alone = self.new_partner('Kit O Sure'), self.new_partner('Kit O Confirm'), self.new_partner('Kit O Alone')
        inv = self.invoice(sure, 300)
        pay = self.payment(sure, inv.amount_total, 'Payment %s' % inv.name)
        self.invoice(confirm, 200)
        self.invoice(confirm, 150)
        self.payment(confirm, 200)
        self.invoice(alone, 50)
        rows = self.rows()
        self.assertEqual(rows[self.key(sure)]['group'], 'sure')
        self.assertEqual(rows[self.key(confirm)]['group'], 'confirm')
        self.assertNotIn(self.key(alone), rows)
        self.assertEqual(self.Items.kit_open_accept_sure([self.key(sure), self.key(confirm)]), 1)
        self.assertEqual(inv.payment_state, 'paid')
        self.assertTrue(pay.reconciled)
        self.assertNotIn(self.key(sure), self.rows())
        self.assertIn(self.key(confirm), self.rows())

    def test_credit_note_and_several_invoices(self):
        """Invoice against a credit note; several invoices against one
        payment (suggested, then reconciled from the drawer)."""
        partner = self.new_partner('Kit O Many')
        a, b = self.invoice(partner, 100), self.invoice(partner, 250)
        pay = self.payment(partner, 350)
        drawer = self.Items.kit_open_partner(partner.id, self.receivable.id)
        self.assertEqual(set(drawer['selected']), set((self.term_line(a) | self.term_line(b) | pay).ids))
        self.Items.kit_open_validate(self.selection(partner, self.term_line(a) | self.term_line(b) | pay))
        self.assertEqual((a | b).mapped('payment_state'), ['paid', 'paid'])
        other = self.new_partner('Kit O Refund')
        invoice = self.invoice(other, 80)
        refund = self.invoice(other, 80, 'out_refund')
        self.Items.kit_open_validate(self.selection(other, self.term_line(invoice) | self.term_line(refund)))
        self.assertIn(invoice.payment_state, ('paid', 'reversed'))
        self.assertIn(refund.payment_state, ('paid', 'reversed'))
        self.assertTrue(self.term_line(invoice).reconciled)

    def test_partial_and_writeoff(self):
        """Keep the rest open (partial); write off the difference to an
        account with a tax: entry posted as previewed, items reconciled."""
        partner = self.new_partner('Kit O Write-off')
        inv = self.invoice(partner, 100)
        pay = self.payment(partner, 60)
        self.Items.kit_open_validate(self.selection(partner, self.term_line(inv) | pay, gap='open'))
        self.assertEqual(inv.payment_state, 'partial')
        self.assertAmount(inv.amount_residual, 40)
        pay2 = self.payment(partner, 28.5)
        selection = self.selection(partner, self.term_line(inv) | pay2, gap='writeoff', writeoffs=[
            {'account_id': self.fees.id, 'amount': 0, 'tax_ids': self.tax_purchase_a.ids, 'label': 'Small difference'}])
        preview = self.Items.kit_open_preview(selection)
        self.assertFalse(preview['error'])
        self.Items.kit_open_validate(selection)
        self.assertEqual(inv.payment_state, 'paid')
        writeoff = self.env['account.move'].search([('ref', 'like', 'Write-off Kit O Write-off')])
        self.assertEqual(writeoff.state, 'posted')
        self.assertEqual(writeoff.journal_id, self.misc)
        self.assertEqual(len(writeoff.line_ids.filtered('tax_line_id')), 1)
        posted = sorted((round(l.debit, 2), round(l.credit, 2)) for l in writeoff.line_ids)
        shown = sorted((round(l['debit'], 2), round(l['credit'], 2)) for l in preview['lines'])
        self.assertEqual(shown, posted)

    def test_model_and_lock_date(self):
        """Write-off with a model; a write-off dated in a locked period is
        moved after the lock date (core)."""
        model = self.env['account.reconcile.model'].create({'name': 'Kit O model', 'line_ids': [
            Command.create({'account_id': self.fees.id, 'amount_type': 'percentage', 'amount_string': '100'})]})
        partner = self.new_partner('Kit O Model')
        inv = self.invoice(partner, 100)
        pay = self.payment(partner, 97)
        self.Items.kit_open_validate(self.selection(partner, self.term_line(inv) | pay, gap='model', model_id=model.id))
        self.assertEqual(inv.payment_state, 'paid')
        self.assertTrue(self.env['account.move.line'].search([('reconcile_model_id', '=', model.id)]))
        other = self.new_partner('Kit O Locked')
        inv2 = self.invoice(other, 100)
        pay2 = self.payment(other, 99)
        lock = self.today - timedelta(days=1)
        self.company.fiscalyear_lock_date = lock
        self.Items.kit_open_validate(self.selection(
            other, self.term_line(inv2) | pay2, gap='model', model_id=model.id,
            date=str(self.today - timedelta(days=5))))
        writeoff = self.env['account.move'].search([('ref', 'like', 'Write-off Kit O Locked')])
        self.assertGreater(writeoff.date, lock)
        self.assertEqual(inv2.payment_state, 'paid')

    def test_early_payment_discount(self):
        """A payment of the discounted amount in time: sure, booked as the
        early payment discount (core helper)."""
        partner = self.new_partner('Kit O EPD')
        inv = self.invoice(partner, 750, term=self.env.ref('account.account_payment_term_30days_early_discount'))
        self.payment(partner, 735)
        row = self.rows()[self.key(partner)]
        self.assertEqual(row['group'], 'sure')
        self.assertIn('Early payment discount', row['reasons'])
        self.Items.kit_open_accept_sure([self.key(partner)])
        self.assertEqual(inv.payment_state, 'paid')
        loss = self.company.account_journal_early_pay_discount_loss_account_id
        self.assertTrue(self.env['account.move.line'].search([('account_id', '=', loss.id), ('partner_id', '=', partner.id)]))

    def test_journal_items_action(self):
        """Reconcile on the journal items list: items that net to zero are
        reconciled; otherwise the Open Items screen opens with them."""
        partner = self.new_partner('Kit O Action')
        inv = self.invoice(partner, 120)
        pay = self.payment(partner, 120)
        result = (self.term_line(inv) | pay).action_kit_reconcile()
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(inv.payment_state, 'paid')
        inv2 = self.invoice(partner, 90)
        pay2 = self.payment(partner, 40)
        action = (self.term_line(inv2) | pay2).action_kit_reconcile()
        self.assertEqual(action['tag'], 'kit_bank_reconciliation')
        self.assertEqual(action['params']['selected'], (self.term_line(inv2) | pay2).ids)
        with self.assertRaises(UserError):
            (self.term_line(inv2) | inv2.line_ids.filtered(lambda l: l.account_id != self.receivable)[:1]).action_kit_reconcile()

    def test_access_rights(self):
        """A user without accounting rights cannot match."""
        partner = self.new_partner('Kit O Rights')
        inv = self.invoice(partner, 10)
        pay = self.payment(partner, 10)
        user = new_test_user(self.env, login='kit_open_noacc', groups='base.group_user')
        with self.assertRaises(AccessError):
            self.Items.with_user(user).kit_open_validate(self.selection(partner, self.term_line(inv) | pay))
