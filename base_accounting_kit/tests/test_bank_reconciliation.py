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
import base64
from unittest.mock import patch

from odoo import Command
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestBankReconciliation(AccountingKitTestCommon):
    """P2.1-a: matched reconcile model on statement lines, auto-reconcile
    (automatic models only, by reference, one savepoint per line, after
    import behind a setting) and the Bank Reconciliation report."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bank = cls.company_data['default_journal_bank']
        cls.fees = cls.env['account.account'].create({'name': 'Kit bank fees', 'code': 'KBFEE', 'account_type': 'expense'})

    def statement_line(self, amount, label, partner=None):
        return self.env['account.bank.statement.line'].create({
            'journal_id': self.bank.id, 'date': self.today, 'payment_ref': label, 'amount': amount,
            'partner_id': partner.id if partner else False})

    def fee_model(self, trigger):
        return self.env['account.reconcile.model'].create({
            'name': 'Kit fees', 'trigger': trigger, 'match_label': 'contains', 'match_label_param': 'FEE',
            'line_ids': [Command.create({'account_id': self.fees.id, 'amount_type': 'percentage',
                                         'amount_string': '100'})]})

    def invoice(self, amount, partner=None):
        return self.init_invoice('out_invoice', partner=partner or self.partner_a, amounts=[amount],
                                 invoice_date=self.today, post=True)

    # ------------------------------------------------------------------
    def test_matched_model_name(self):
        """The matched manual model and its name are computed together
        (no related field on a non-stored compute)."""
        model = self.fee_model('manual')
        line = self.statement_line(-12, 'BANK FEE NOV')
        self.assertEqual(line.matched_reconcile_model_id, model)
        self.assertEqual(line.matched_reconcile_model_name, 'Kit fees')
        field = self.env['account.bank.statement.line']._fields['matched_reconcile_model_name']
        self.assertFalse(field.related)

    def test_auto_reconcile_uses_automatic_models_only(self):
        """A model meant to be clicked by hand is not applied by
        auto-reconcile; an automatic one is."""
        model = self.fee_model('manual')
        line = self.statement_line(-12, 'BANK FEE NOV')
        line._auto_reconcile()
        self.assertFalse(line.is_reconciled)
        model.trigger = 'auto_reconcile'
        line._auto_reconcile()
        self.assertTrue(line.is_reconciled)

    def test_auto_reconcile_by_reference(self):
        """Without a partner, the invoice whose number is in the label (and
        has the amount) is matched and gives the partner; without a unique
        mention nothing happens."""
        invoice = self.invoice(1000)
        self.invoice(1000, self.partner_b)
        amount = invoice.amount_total
        line = self.statement_line(amount, 'Payment %s thank you' % invoice.name)
        unclear = self.statement_line(amount, 'Payment without reference')
        (line | unclear)._auto_reconcile()
        self.assertTrue(line.is_reconciled)
        self.assertEqual(line.partner_id, self.partner_a)
        self.assertEqual(invoice.payment_state, 'paid')
        self.assertFalse(unclear.is_reconciled)

    @mute_logger('odoo.addons.base_accounting_kit.models.account_bank_statement_line')
    def test_auto_reconcile_savepoint(self):
        """A line that fails is skipped; the others are still reconciled."""
        self.fee_model('auto_reconcile')
        bad = self.statement_line(-5, 'FEE A')
        good = self.statement_line(-7, 'FEE B')
        original = type(bad)._get_reconcile_proposal

        def proposal(record, *args, **kwargs):
            if record == bad:
                raise ValueError('broken line')
            return original(record, *args, **kwargs)
        with patch.object(type(bad), '_get_reconcile_proposal', proposal):
            done = (bad | good)._auto_reconcile()
        self.assertEqual(done, good)
        self.assertTrue(good.is_reconciled)
        self.assertFalse(bad.is_reconciled)

    def test_import_setting(self):
        """After an import, transactions are reconciled automatically only
        when the company setting is on (off by default)."""
        self.assertFalse(self.company.kit_auto_reconcile_import)

        def import_csv(name, invoice):
            content = 'date,label,amount\n%s,Payment %s,%s\n' % (self.today, invoice.name, invoice.amount_total)
            wizard = self.env['import.bank.statement'].create({
                'attachment': base64.b64encode(content.encode()).decode(), 'file_name': name,
                'journal_id': self.bank.id})
            return wizard.action_statement_import()
        first = self.invoice(500)
        import_csv('first.csv', first)
        self.assertNotEqual(first.payment_state, 'paid')
        self.company.kit_auto_reconcile_import = True
        second = self.invoice(600)
        action = import_csv('second.csv', second)
        self.assertEqual(second.payment_state, 'paid')
        self.assertIn('1 reconciled automatically', action['params']['message'])

    # ------------------------------------------------------------------
    def test_bank_reconciliation_report(self):
        """Bank side: statement balance + receipts / payments not on the
        statement; books side: book balance + unreconciled transactions;
        the difference shows an entry booked on the bank account without a
        statement line."""
        invoice = self.invoice(1000)
        matched = self.statement_line(invoice.amount_total, 'Payment %s' % invoice.name)
        matched._auto_reconcile()
        self.assertTrue(matched.is_reconciled)
        self.statement_line(250, 'Unknown deposit')
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound', 'partner_type': 'customer', 'partner_id': self.partner_b.id,
            'amount': 800, 'journal_id': self.bank.id, 'date': self.today})
        payment.action_post()
        self.kit_entry(self.today, [(self.bank.default_account_id, 50, 0), (self.kit_account('income'), 0, 50)])
        report = self.dyn('bank_reconciliation')
        result = report.get_report({'journal_ids': self.bank.ids})
        lines = self.by_id(result)
        jid = self.bank.id
        statement = invoice.amount_total + 250
        self.assertAmount(lines['statement_%s' % jid]['columns'][0], statement)
        self.assertAmount(lines['receipts_%s' % jid]['columns'][0], 800)
        self.assertAmount(lines['payments_%s' % jid]['columns'][0], 0)
        self.assertAmount(lines['adjustedbank_%s' % jid]['columns'][0], statement + 800)
        self.assertAmount(lines['unreconciled_%s' % jid]['columns'][0], 250)
        self.assertAmount(lines['books_%s' % jid]['columns'][0], statement + 50 - 250 + 800)
        self.assertAmount(lines['adjustedbooks_%s' % jid]['columns'][0], statement + 50 + 800)
        self.assertAmount(lines['difference_%s' % jid]['columns'][0], -50)
        receipts = report.get_lines({'journal_ids': self.bank.ids}, 'receipts_%s' % jid)
        self.assertEqual(len(receipts), 1)
        self.assertAmount(receipts[0]['columns'][0], 800)
        unreconciled = report.get_lines({'journal_ids': self.bank.ids}, 'unreconciled_%s' % jid)
        self.assertEqual(len(unreconciled), 1)
        self.assertIn('Unknown deposit', unreconciled[0]['name'])
        self.assertEqual(result['date_mode'], 'single')
        journals = self.env['account.journal'].browse([j['id'] for j in result['journals']])
        self.assertEqual(set(journals.mapped('type')), {'bank', 'cash'})
        self.assertIn('Bank Reconciliation', self.pdf_html('bank_reconciliation', {'journal_ids': self.bank.ids}))
        menu = self.env.ref('base_accounting_kit.menu_bank_reconciliation_report')
        self.assertEqual(menu.parent_id, self.env.ref('base_accounting_kit.account_reports_audit'))
