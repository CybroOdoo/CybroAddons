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
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools.safe_eval import safe_eval

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestJournalEntryReport(AccountingKitTestCommon):
    """Journal Entry PDF (P3.7): letterhead, status, columns only when
    used, tax summary, notes, signature block; journal entries only."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.external_report_layout_id = cls.env.ref('web.external_layout_standard')
        cls.report = cls.env.ref('base_accounting_kit.action_report_journal_entry')

    def html(self, moves):
        return self.env['ir.actions.report']._render_qweb_html(self.report.report_name, moves.ids)[0].decode()

    def test_rich_entry(self):
        """An entry with partner, analytic, tax and a foreign currency line
        shows all columns, the tax summary, the note and the signatures."""
        eur = self.env.ref('base.EUR')
        eur.active = True
        plan = self.env['account.analytic.plan'].create({'name': 'Kit JE plan'})
        analytic = self.env['account.analytic.account'].create({'name': 'Kit Administration', 'plan_id': plan.id})
        tax = self.tax_purchase_a
        repartition = tax.invoice_repartition_line_ids.filtered(lambda r: r.repartition_type == 'tax')
        move = self.env['account.move'].create({
            'move_type': 'entry', 'date': self.today, 'ref': 'Office rent',
            'narration': '<p>Rent for the month.</p>',
            'line_ids': [
                Command.create({'account_id': self.kit_account('expense').id, 'partner_id': self.partner_a.id,
                                'name': 'Office rent', 'debit': 1000, 'tax_ids': [Command.set(tax.ids)],
                                'analytic_distribution': {str(analytic.id): 100}}),
                Command.create({'account_id': repartition.account_id.id, 'name': tax.name, 'debit': 150,
                                'tax_line_id': tax.id, 'tax_base_amount': 1000,
                                'tax_repartition_line_id': repartition.id}),
                Command.create({'account_id': self.kit_account('liability_payable').id, 'partner_id': self.partner_a.id,
                                'name': 'Rent payable', 'credit': 1150, 'currency_id': eur.id, 'amount_currency': -1050})]})
        move.action_post()
        html = self.html(move)
        for text in ('Partner', 'Analytic', 'Taxes', 'Foreign amount', 'Kit Administration', 'Tax summary',
                     'Rent for the month.', 'Prepared by', 'Checked by', 'Approved by', 'Posted'):
            self.assertIn(text, html, text)
        self.assertEqual(safe_eval(self.report.print_report_name, {'object': move}), move.name)

    def test_plain_draft_entry(self):
        """A plain draft entry hides unused columns and is named
        "Draft Entry"."""
        move = self.kit_entry(self.today, [(self.kit_account('expense'), 300, 0),
                                           (self.kit_account('liability_payable'), 0, 300)], post=False)
        html = self.html(move)
        for text in ('>Partner<', '>Analytic<', '>Taxes<', 'Foreign amount', 'Tax summary'):
            self.assertNotIn(text, html, text)
        self.assertIn('Draft Entry', html)
        self.assertEqual(safe_eval(self.report.print_report_name, {'object': move}), 'Draft Entry')

    def test_entries_only(self):
        """Not offered on invoices (domain) and refused for them."""
        invoice = self.init_invoice('out_invoice', products=self.product_a, post=True)
        entry = self.kit_entry(self.today, [(self.kit_account('expense'), 5, 0), (self.kit_account('asset_current'), 0, 5)])
        matching = self.env['account.move'].search(safe_eval(self.report.domain) + [('id', 'in', (invoice | entry).ids)])
        self.assertEqual(matching, entry)
        with self.assertRaises(UserError):
            self.html(invoice)
