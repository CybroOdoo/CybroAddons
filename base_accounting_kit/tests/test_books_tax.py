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
from odoo.tests import tagged

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestBooksAndTax(AccountingKitTestCommon):
    """Tax Report (P1.5), Day / Cash / Bank Book and Journals Audit (P1.6,
    SP.4): figures and signs, target moves, journals, accounts filter,
    comparison, unfold, exports."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.s15 = cls.tax_sale_a
        cls.p15 = cls.tax_purchase_a
        cls.s0 = cls.env['account.tax'].create({
            'name': 'Kit 0%', 'amount': 0, 'amount_type': 'percent', 'type_tax_use': 'sale',
            'company_id': cls.company.id})
        cls.customer = cls.env['res.partner'].create({'name': 'Kit Tax Customer'})
        cls.vendor = cls.env['res.partner'].create({'name': 'Kit Tax Vendor'})
        cls.day = cls.ymd(3, 1)
        cls.inv1 = cls.invoice('out_invoice', cls.customer, 1000, cls.s15)
        cls.invoice('out_refund', cls.customer, 200, cls.s15)
        cls.invoice('out_invoice', cls.customer, 500, cls.s0)
        cls.invoice('in_invoice', cls.vendor, 400, cls.p15)
        cls.invoice('out_invoice', cls.customer, 300, cls.s15, state='draft')
        cls.invoice('out_invoice', cls.customer, 700, cls.s15, state='cancel')

    @classmethod
    def invoice(cls, move_type, partner, amount, tax, state='posted', day=None):
        move = cls.env['account.move'].create({
            'move_type': move_type, 'partner_id': partner.id,
            'invoice_date': day or cls.day,
            'invoice_line_ids': [Command.create({
                'name': 'x', 'quantity': 1, 'price_unit': amount, 'tax_ids': [Command.set(tax.ids)]})]})
        if state in ('posted', 'cancel'):
            move.action_post()
        if state == 'cancel':
            move.button_draft()
            move.button_cancel()
        return move

    def tax_figures(self, **options):
        res, section = {}, None
        for line in self.dyn('tax').get_report(options)['lines']:
            if line['id'].startswith('section_'):
                section = line['id'][8:]
                res[('total', section)] = tuple(line['columns'][:2])
            else:
                res[(section, line['name'])] = tuple(line['columns'][:2])
        return res

    # ------------------------------------------------------------------ Tax
    def test_tax_report_figures(self):
        """Posted figures with signs (refund deducted), 0% tax listed,
        Sales / Purchases totals; draft only with "All entries", cancelled
        never; journal filter; archived taxes still listed."""
        figures = self.tax_figures(target_move='posted')
        self.assertAmount(figures[('sale', self.s15.name)][0], 800)
        self.assertAmount(figures[('sale', self.s15.name)][1], 120)
        self.assertAmount(figures[('sale', self.s0.name)][0], 500)
        self.assertAmount(figures[('purchase', self.p15.name)][0], 400)
        self.assertAmount(figures[('purchase', self.p15.name)][1], 60)
        self.assertAmount(figures[('total', 'sale')][0], 1300)
        self.assertAmount(figures[('total', 'sale')][1], 120)
        all_entries = self.tax_figures(target_move='all')
        self.assertAmount(all_entries[('sale', self.s15.name)][0], 1100)
        self.assertAmount(all_entries[('sale', self.s15.name)][1], 165)
        purchases = self.tax_figures(journal_ids=self.kit_journal('purchase').ids)
        self.assertFalse([key for key in purchases if key[0] == 'sale'])
        self.p15.active = False
        self.assertIn(('purchase', self.p15.name), self.tax_figures())

    def test_tax_report_comparison_and_drill(self):
        """Comparison with last year and variance; a tax line opens its
        journal items."""
        self.invoice('out_invoice', self.customer, 400, self.s15, day=self.ymd(3, 1, 1))
        report = self.dyn('tax').get_report({'comparison': {'periods': 1}})
        line = self.by_id(report)['tax_%s' % self.s15.id]
        self.assertEqual(line['columns'], [800, 120, 60, 60])
        action = self.dyn('tax').action_open_line({}, 'tax_%s' % self.s15.id)
        self.assertEqual(action['res_model'], 'account.move.line')
        self.assertIn(('tax_ids', 'in', [self.s15.id]),
                      [tuple(d) for d in action['domain'] if isinstance(d, (list, tuple))])
        html = self.pdf_html('tax', {})
        self.assertIn('1,300.00', html)
        rows = [[cell.value for cell in row] for row in self.xlsx_sheet('tax', {}).iter_rows()]
        self.assertTrue(any(row[0] == 'Sales' and row[1] == 1300 for row in rows))

    def test_tax_report_group_of_taxes(self):
        """A group of taxes (e.g. CGST + SGST, any localisation): the group
        line with the base and the children's tax, each child with the base
        of the group and its own tax, the base counted once in the total;
        single taxes unchanged; drill-down of group and child."""
        children = self.env['account.tax'].create([{
            'name': 'Kit %s 5%%' % name, 'amount': 5, 'amount_type': 'percent', 'type_tax_use': 'none',
            'company_id': self.company.id} for name in ('State', 'Central')])
        group = self.env['account.tax'].create({
            'name': 'Kit GST 10%', 'amount_type': 'group', 'type_tax_use': 'sale', 'company_id': self.company.id,
            'children_tax_ids': [Command.set(children.ids)]})
        self.invoice('out_invoice', self.customer, 2000, group)
        report = self.dyn('tax').get_report({})
        lines = self.by_id(report)
        self.assertEqual(lines['tax_%s' % group.id]['columns'][:2], [2000, 200])
        self.assertEqual(lines['tax_%s' % group.id]['level'], 1)
        for child in children:
            child_line = lines['tax_%s_%s' % (child.id, group.id)]
            self.assertEqual((child_line['columns'][:2], child_line['level']), ([2000, 100], 2))
        figures = self.tax_figures()
        self.assertAmount(figures[('total', 'sale')][0], 1300 + 2000)
        self.assertAmount(figures[('total', 'sale')][1], 120 + 200)
        self.assertAmount(figures[('sale', self.s15.name)][0], 800)
        action = self.dyn('tax').action_open_line({}, 'tax_%s_%s' % (children[0].id, group.id))
        domain = [tuple(d) for d in action['domain'] if isinstance(d, (list, tuple))]
        self.assertIn(('tax_ids', 'in', group.ids), domain)
        self.assertIn(('tax_line_id', 'in', children[0].ids), domain)
        items = self.env['account.move.line'].search(action['domain'])
        self.assertEqual(len(items), 2)  # the base line and the child's tax line

    def test_tax_report_cash_basis(self):
        """A tax based on payment counts when the invoice is paid (core
        cash basis entry), in proportion to the payment, not on the
        invoice; its drill-down lists the cash basis entry only."""
        self.company.tax_exigibility = True
        transition = self.env['account.account'].create({
            'code': 'KITCABA', 'name': 'Kit cash basis transition', 'account_type': 'liability_current',
            'reconcile': True, 'company_ids': [Command.set(self.company.ids)]})
        caba = self.env['account.tax'].create({
            'name': 'Kit CABA 10%', 'amount': 10, 'amount_type': 'percent', 'type_tax_use': 'sale',
            'tax_exigibility': 'on_payment', 'cash_basis_transition_account_id': transition.id,
            'company_id': self.company.id})
        invoice = self.invoice('out_invoice', self.customer, 1000, caba, day=self.ymd(1, 10))
        self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoice.ids).create({
                'amount': 550, 'payment_date': self.ymd(2, 10)})._create_payments()

        def figures(month):
            start = self.ymd(month, 1)
            end = self.ymd(month + 1, 1) - timedelta(days=1)
            return self.tax_figures(date_preset='custom', date_from=str(start), date_to=str(end))
        self.assertNotIn(('sale', caba.name), figures(1))
        net, tax = figures(2)[('sale', caba.name)]
        self.assertAmount(net, 500)
        self.assertAmount(tax, 50)
        action = self.dyn('tax').action_open_line(
            {'date_preset': 'custom', 'date_from': str(self.ymd(1, 1)), 'date_to': str(self.ymd(2, 28))},
            'tax_%s' % caba.id)
        items = self.env['account.move.line'].search(action['domain'])
        self.assertTrue(items)
        self.assertTrue(all(items.move_id.mapped('tax_cash_basis_rec_id')))

    def test_tax_report_withholding(self):
        """With core's withholding module, withholding taxes have their own
        section, left out of Sales and Purchases."""
        if 'is_withholding_tax' not in self.env['account.tax']._fields:
            self.skipTest("l10n_account_withholding_tax is not installed")
        wht = self.env['account.tax'].create({
            'name': 'Kit WHT 2%', 'amount': -2, 'amount_type': 'percent', 'type_tax_use': 'purchase',
            'is_withholding_tax': True, 'company_id': self.company.id})
        repartition = wht.invoice_repartition_line_ids.filtered(lambda l: l.repartition_type == 'tax')
        tax_account = repartition.account_id or self.kit_account('liability_current')
        self.env['account.move'].create({
            'move_type': 'entry', 'date': self.day, 'journal_id': self.kit_journal('general').id,
            'line_ids': [
                Command.create({'account_id': self.kit_account('liability_payable').id, 'debit': 20, 'name': 'wht'}),
                Command.create({'account_id': tax_account.id, 'credit': 20, 'name': 'wht',
                                'tax_line_id': wht.id, 'tax_repartition_line_id': repartition.id}),
            ]}).action_post()
        figures = self.tax_figures()
        self.assertIn(('withholding', wht.name), figures)
        self.assertAmount(figures[('total', 'withholding')][1], -20)
        self.assertNotIn(('purchase', wht.name), figures)
        self.assertAmount(figures[('total', 'purchase')][1], 60)

    # ------------------------------------------------------------------ Books
    def test_day_book(self):
        """Day Book: one line per day with its items; accounts filter;
        forged account ids dropped."""
        report = self.dyn('day_book')
        options = {'date_preset': 'custom', 'date_from': str(self.day), 'date_to': str(self.day)}
        day_line = self.by_id(report.get_report(options))['day_%s' % self.day]
        self.assertGreater(day_line['columns'][0], 0)
        self.assertAmount(day_line['columns'][0], day_line['columns'][1])
        receivable = self.inv1.line_ids.filtered(lambda l: l.account_id.account_type == 'asset_receivable').account_id
        filtered = report.get_report(dict(options, account_ids=receivable.ids))
        self.assertAmount(filtered['lines'][0]['columns'][1], 230)  # refund 200 + 15% tax
        self.assertEqual(report.get_report({'account_ids': [999999999]})['options']['account_ids'], [])

    def test_bank_book(self):
        """Bank Book: initial balance by default, unfold with the opening
        line and running balance, accounts filter limited to cash/bank."""
        bank = self.kit_journal('bank').default_account_id
        income = self.kit_account('income')
        self.kit_entry(self.ymd(12, 1, 1), [(bank, 300, 0), (income, 0, 300)])
        self.kit_entry(self.ymd(2, 1), [(bank, 50, 0), (income, 0, 50)])
        report = self.dyn('bank_book')
        result = report.get_report({})
        self.assertAmount(self.by_id(result)['account_%s' % bank.id]['columns'][2], 350)
        without = report.get_report({'initial_balance': False})
        self.assertAmount(self.by_id(without)['account_%s' % bank.id]['columns'][2], 50)
        children = report.get_lines({}, 'account_%s' % bank.id)
        self.assertTrue(children[0]['id'].startswith('init_'))
        self.assertAmount(children[-1]['columns'][2], 350)
        self.assertIn(tuple(result['account_domain'][0]), {('account_type', '=', 'asset_cash')})
        self.assertIn(350, self.sheet_values(self.xlsx_sheet('bank_book', {})))

    def test_book_debit_credit_of_the_period(self):
        """QA Q1: Bank and Cash Book show the period's debit and credit (as
        the General Ledger), the earlier years only in the balance; the
        Total adds the balances."""
        bank = self.kit_journal('bank').default_account_id
        cash = self.kit_journal('cash').default_account_id
        income = self.kit_account('income')
        self.kit_entry(self.ymd(6, 1, 1), [(bank, 1000, 0), (income, 0, 1000)])
        self.kit_entry(self.ymd(7, 1, 1), [(income, 400, 0), (bank, 0, 400)])
        self.kit_entry(self.ymd(2, 1), [(bank, 70, 0), (income, 0, 70)])
        self.kit_entry(self.ymd(6, 1, 1), [(cash, 90, 0), (income, 0, 90)])
        self.kit_entry(self.ymd(2, 2), [(income, 15, 0), (cash, 0, 15)])
        year = {'date_preset': 'custom', 'date_from': str(self.ymd(1, 1)), 'date_to': str(self.ymd(12, 31))}
        for name, account, expected in (('bank_book', bank, [70, 0, 670]), ('cash_book', cash, [0, 15, 75])):
            lines = self.by_id(self.dyn(name).get_report(year))
            for value, amount in zip(lines['account_%s' % account.id]['columns'], expected):
                self.assertAmount(value, amount, name)
            total = lines['total']['columns']
            self.assertAmount(total[2], sum(line['columns'][2] for key, line in lines.items() if key != 'total'))
            gl = self.by_id(self.dyn('general_ledger').get_report(dict(year, account_ids=account.ids)))
            self.assertEqual([round(x, 2) for x in gl['account_%s' % account.id]['columns']],
                             [round(x, 2) for x in lines['account_%s' % account.id]['columns']])

    def test_book_without_journal(self):
        """A company without cash journal: the Cash Book opens empty and
        says to choose the accounts (no error, also in Excel); with an
        account chosen it shows it."""
        self.env['account.journal'].search([('company_id', '=', self.company.id), ('type', '=', 'cash')]).active = False
        report = self.dyn('cash_book')
        result = report.get_report({})
        self.assertEqual([line['id'] for line in result['lines']], ['total'])
        self.assertIn('No cash journal for %s' % self.company.name, result['notice'])
        self.assertTrue(self.xlsx_sheet('cash_book', {}))
        bank = self.kit_journal('bank').default_account_id
        self.kit_entry(self.ymd(2, 1), [(bank, 40, 0), (self.kit_account('income'), 0, 40)])
        chosen = report.get_report({'account_ids': bank.ids})
        self.assertFalse(chosen['notice'])
        self.assertAmount(self.by_id(chosen)['account_%s' % bank.id]['columns'][2], 40)
        self.assertFalse(self.dyn('bank_book').get_report({})['notice'])

    def test_journals_audit(self):
        """Journals Audit: journals with entries and a total; unfold shows
        the items and a tax summary; sort option."""
        sale = self.kit_journal('sale')
        report = self.dyn('journal_audit')
        result = report.get_report({})
        self.assertIn('journal_%s' % sale.id, self.by_id(result))
        self.assertEqual(result['lines'][-1]['id'], 'total')
        children = report.get_lines({}, 'journal_%s' % sale.id)
        self.assertTrue([c for c in children if c['id'].startswith('aml_')])
        self.assertTrue([c for c in children if c['id'].startswith('taxsum_')])
        self.assertEqual([d['key'] for d in result['option_defs']], ['sort_selection'])
