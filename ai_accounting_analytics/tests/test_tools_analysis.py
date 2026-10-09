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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from freezegun import freeze_time

from odoo.tests import new_test_user, tagged

from .common import AiAccountingCommon


@tagged('post_install', '-at_install')
@freeze_time('2026-10-15')
class TestAnalysisTools(AiAccountingCommon):
    """Breakdowns, comparisons, margins, forecast, ratios and detail lookups."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a.country_id = cls.env.ref('base.be')
        cls.partner_b.country_id = cls.env.ref('base.us')
        cls.seller = new_test_user(cls.env, login='ai_seller', name='Seller Sam')
        plan = cls.env['account.analytic.plan'].create({'name': 'Projects'})
        cls.project = cls.env['account.analytic.account'].create({'name': 'Project X', 'plan_id': plan.id})

        cls.inv_product = cls._invoice('out_invoice', cls.partner_a, '2026-10-05', '2026-10-10',
                                       products=cls.product_a, analytic=cls.project)
        cls.inv_b = cls._invoice('out_invoice', cls.partner_b, '2026-10-06', '2026-10-20',
                                 amount=500.0, user=cls.seller)
        cls.bill = cls._invoice('in_invoice', cls.partner_b, '2026-10-07', '2026-10-21', amount=300.0)
        cls.inv_sep = cls._invoice('out_invoice', cls.partner_a, '2026-09-10', '2026-09-10', amount=200.0)

    @classmethod
    def _invoice(cls, move_type, partner, invoice_date, due_date, amount=None, products=None,
                 user=None, analytic=None):
        move = cls.init_invoice(move_type, partner, invoice_date, taxes=[],
                                amounts=[amount] if amount else None, products=products)
        move.write({'invoice_payment_term_id': False, 'invoice_date_due': due_date})
        move.invoice_line_ids.tax_ids = False
        if user:
            move.invoice_user_id = user
        if analytic:
            move.invoice_line_ids.analytic_distribution = {str(analytic.id): 100}
        move.action_post()
        return move

    def run_tool(self, name, **arguments):
        output = self.toolkit._ai_run_tool(name, arguments)
        self.assertFalse(output.get('error'), output['model'])
        return output

    def rows(self, output):
        return {row[0]: row for row in output['model']['rows']}

    # Breakdowns ------------------------------------------------------
    def test_sales_by_partner_and_country(self):
        output = self.run_tool('get_breakdown', measure='sales', group_by='partner', period='this_month')
        rows = self.rows(output)
        self.assertEqual(rows[self.partner_a.display_name][1], 1000.0)
        self.assertEqual(rows[self.partner_b.display_name][1], 500.0)
        self.assertEqual(output['model']['total'], 1500.0)
        output = self.run_tool('get_breakdown', measure='sales', group_by='country', period='this_month')
        rows = self.rows(output)
        self.assertEqual(rows['Belgium'][1], 1000.0)
        self.assertEqual(rows['United States'][1], 500.0)

    def test_sales_by_salesperson(self):
        output = self.run_tool('get_breakdown', measure='sales', group_by='salesperson', period='this_month')
        self.assertEqual(self.rows(output)['Seller Sam'][1], 500.0)

    def test_two_dimensions(self):
        output = self.run_tool('get_breakdown', measure='sales', group_by='partner', then_by='month',
                               period='this_year', chart='bar')
        self.assertEqual(output['model']['cols'][-1], 'total')
        row = self.rows(output)[self.partner_a.display_name]
        self.assertEqual(row[-1], 1200.0)
        self.assertIn(200.0, row[1:-1])
        chart = next(block for block in output['blocks'] if block['type'] == 'chart')
        self.assertEqual(len(chart['datasets']), 2)

    def test_time_dimension_is_chronological(self):
        output = self.run_tool('get_breakdown', measure='revenue', group_by='month', period='this_year')
        values = [row[1] for row in output['model']['rows']]
        self.assertEqual(values, [200.0, 1500.0])

    def test_expenses_by_account(self):
        output = self.run_tool('get_breakdown', measure='expenses', group_by='account', period='this_month')
        self.assertEqual(output['model']['total'], 300.0)

    def test_revenue_by_analytic_account(self):
        output = self.run_tool('get_breakdown', measure='revenue', group_by='analytic_account',
                               period='this_month')
        self.assertEqual(self.rows(output)['Project X'][1], 1000.0)

    def test_breakdown_errors(self):
        output = self.toolkit._ai_run_tool('get_breakdown', {'measure': 'sales', 'group_by': 'planet'})
        self.assertTrue(output['error'])
        output = self.toolkit._ai_run_tool('get_breakdown', {
            'measure': 'sales', 'group_by': 'analytic_account', 'then_by': 'country'})
        self.assertTrue(output['error'])

    # Analysis ---------------------------------------------------------
    def test_compare_periods(self):
        output = self.run_tool('compare_periods', period_a='this_month', period_b='last_month')
        rows = self.rows(output)
        self.assertEqual(rows['revenue'][1:3], [1500.0, 200.0])
        self.assertEqual(rows['profit'][1:4], [1200.0, 200.0, 1000.0])
        self.assertEqual(output['model']['invoices_a'], 2)
        output = self.run_tool('compare_periods', period_a='custom', a_from='2026-10-01', a_to='2026-10-05',
                               period_b='custom', b_from='2026-09-01', b_to='2026-09-30')
        self.assertEqual(self.rows(output)['sales'][1:3], [1000.0, 200.0])

    def test_margins(self):
        output = self.run_tool('get_margins', group_by='product', period='this_month')
        row = self.rows(output)[self.product_a.display_name]
        self.assertEqual(row[1:], [1000.0, 800.0, 200.0, 20.0])
        output = self.run_tool('get_margins', group_by='customer', period='this_month')
        self.assertEqual(self.rows(output)[self.partner_a.display_name][3], 200.0)

    def test_cash_forecast(self):
        output = self.run_tool('get_cash_forecast', granularity='week', periods=4)
        model = output['model']
        self.assertEqual(len(model['rows']), 4)
        self.assertEqual(model['overdue_in'], 1200.0, "Sep invoice and the one due 10-10")
        expected_in = {row[0]: row[1] for row in model['rows']}
        self.assertIn(500.0, expected_in.values())
        self.assertEqual(sum(row[2] for row in model['rows']), 300.0)
        self.assertEqual(model['rows'][-1][4], model['opening_cash'] + 500.0 - 300.0)

    def test_ratios(self):
        output = self.run_tool('get_ratios', period='this_year')
        model = output['model']
        self.assertGreater(model['dso_days'], 0)
        self.assertEqual(model['net_margin_pct'], round((1700.0 - 300.0) / 1700.0 * 100, 1))
        kinds = {item['type'] for item in output['blocks'][0]['items']}
        self.assertEqual(kinds, {'days', 'ratio', 'percent'})

    # Detail lookups ---------------------------------------------------
    def test_payments(self):
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound', 'partner_type': 'customer', 'partner_id': self.partner_b.id,
            'amount': 100.0, 'date': '2026-10-09',
            'journal_id': self.company_data['default_journal_bank'].id})
        payment.action_post()
        output = self.run_tool('get_payments', kind='received', status='all', period='this_month')
        self.assertEqual(output['model']['received'], 100.0)
        self.assertEqual(output['blocks'][0]['rows'][0]['res_id'], payment.id)
        output = self.run_tool('get_payments', kind='sent', status='all', period='this_month')
        self.assertEqual(output['model']['count'], 0)

    def test_search_journal_items(self):
        output = self.run_tool('search_journal_items', period='this_year', text=self.inv_b.name)
        self.assertTrue(output['model']['count'] >= 2)
        self.assertTrue(all(row[1] == self.inv_b.name for row in output['model']['rows']))
        output = self.run_tool('search_journal_items', period='this_year', min_amount=900)
        self.assertTrue(all(max(row[6], row[7]) >= 900 for row in output['model']['rows']))
        output = self.run_tool('search_journal_items', period='this_year', partner=self.partner_b.name,
                               journal=self.bill.journal_id.code)
        self.assertTrue(all(row[1] == self.bill.name for row in output['model']['rows']))

    def test_invoice_details(self):
        output = self.run_tool('get_invoice_details', number=self.inv_product.name)
        self.assertEqual(output['model']['total'], 1000.0)
        self.assertEqual(output['model']['rows'][0][0], self.product_a.display_name)
        self.assertEqual([block['type'] for block in output['blocks']], ['kpis', 'table'])
        output = self.run_tool('get_invoice_details', number=self.inv_product.name.split('/')[0])
        self.assertTrue(output['model']['ambiguous'])

    def test_unreconciled_bank_lines(self):
        self.env['account.bank.statement.line'].create({
            'journal_id': self.company_data['default_journal_bank'].id, 'date': '2026-10-10',
            'payment_ref': 'Transfer X', 'amount': 250.0})
        output = self.run_tool('get_unreconciled_bank_lines')
        self.assertIn('Transfer X', [row[2] for row in output['model']['rows']])
        self.assertTrue(output['model']['count'] >= 1)
