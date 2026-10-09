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
"""End-to-end question scenarios.

Each scenario is a question a user asks, the tool calls a model makes for it
(written with the quirks real models show: synonyms, other parameter names,
periods in words, numbers as text, unused parameters sent empty) and a check
of the figures the model receives back. The agent loop runs for real; only
the model is scripted.
"""
import json

from freezegun import freeze_time

from odoo.tests import tagged

from odoo.addons.ai_accounting_analytics.llm import LLMResult, ToolCall, Usage

from .common import AiAccountingDataCommon, answer


def step(*items):
    return LLMResult(usage=Usage(input_tokens=100, output_tokens=20), tool_calls=[
        ToolCall(id='call_%s' % index, name=name, arguments=arguments)
        for index, (name, arguments) in enumerate(items)])


@tagged('post_install', '-at_install')
@freeze_time('2026-10-15')
class TestQuestionScenarios(AiAccountingDataCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.tz = 'UTC'
        cls.new_products = cls.env['product.product'].create([{'name': 'AI New %s' % i} for i in range(2)])
        cls.revenue_october = cls.inv_a.amount_untaxed + cls.inv_b.amount_untaxed - cls.refund.amount_untaxed

    def scenario(self, question, steps, check):
        with self.fake_llm(*steps, answer("Here is what I found.")) as fake:
            chat, events = self.ask(question)
        self.assertEqual(events[-1]['type'], 'done')
        message = chat.message_ids.filtered(lambda m: m.role == 'assistant')
        failed = [(item['name'], item.get('error')) for item in message.steps if not item['ok']]
        self.assertFalse(failed, "%s: failed steps %s" % (question, failed))
        self.assertFalse(message.error, question)
        results = [json.loads(result['content']) for call in fake.calls[1:]
                   for result in call['messages'][-1]['results']]
        check(results, message)

    def rows(self, result):
        return {row[0]: row for row in result['rows']}

    def test_scenarios(self):
        revenue_code = self.company_data['default_account_revenue'].code
        unsold = self.new_products
        scenarios = [
            ("What's our profit this month?",
             [step(('get_profit_and_loss', {'period': 'This Month', 'compare': '', 'detail': '', 'chart': ''}))],
             lambda r, m: self.assertEqual(r[0]['period'], '2026-10-01..2026-10-31')),
            ("Revenue this month compared with last month",
             [step(('compare_periods', {'period_a': 'this month', 'period_b': 'previous month'}))],
             lambda r, m: self.assertEqual(r[0]['rows'][0][1:3], [self.revenue_october, 500.0])),
            ("Who are my top 5 customers this year?",
             [step(('get_top_partners', {'kind': 'Customers', 'limit': '5', 'period': 'YTD'}))],
             lambda r, m: self.assertEqual(r[0]['rows'][0][0], self.partner_a.display_name)),
            ("And my top vendors?",
             [step(('get_top_partners', {'type': 'suppliers'}))],
             lambda r, m: self.assertEqual(r[0]['total'], 400.0)),
            ("Which customer invoices are overdue?",
             [step(('get_invoices', {'type': 'customer', 'status': 'late', 'partner': '', 'limit': 0}))],
             lambda r, m: self.assertIn(self.inv_a.name, [row[0] for row in r[0]['rows']])),
            ("How much does Partner A owe us?",
             [step(('get_partner_summary', {'partner_name': self.partner_a.name}))],
             lambda r, m: self.assertEqual(r[0]['receivable'], 3400.0)),
            ("Aged receivables",
             [step(('get_aged_balance', {'kind': 'AR', 'as_of': ''}))],
             lambda r, m: self.assertEqual(r[0]['totals'][-1], 3400.0 + self.inv_b.amount_total - 200.0)),
            ("Sales by country this year as a pie chart",
             [step(('get_breakdown', {'measure': 'Sales', 'group_by': 'countries', 'chart': 'donut',
                                      'period': '2026'}))],
             lambda r, m: (self.assertEqual(set(self.rows(r[0])), {'Belgium', 'United States'}),
                           self.assertIn('pie', [p.get('chart_type') for p in m.parts]))),
            ("Monthly revenue for the last 6 months",
             [step(('get_trend', {'metric': 'revenue', 'granularity': 'monthly', 'period': 'last 6 months'}))],
             lambda r, m: self.assertEqual(r[0]['rows'][-1][1], self.revenue_october)),
            ("Revenue per year",
             [step(('get_trend', {'metric': 'revenue', 'granularity': 'yearly', 'period': 'all_time'}))],
             lambda r, m: self.assertEqual(r[0]['cols'], ['year', 'amount'])),
            ("How many customers do we have?",
             [step(('query_records', {'model': 'res.partner', 'domain': "[('customer_rank', '>', 0)]"}))],
             lambda r, m: self.assertEqual(r[0]['count'], self.env['res.partner'].search_count(
                 [('customer_rank', '>', 0)]))),
            ("How many products created in October?",
             [step(('query_records', {'model': 'product.product', 'period': 'october', 'date_field': 'create_date',
                                      'related': {'mode': 'without', 'model': '', 'field': '', 'domain': ''}}))],
             lambda r, m: self.assertEqual(r[0]['count'], self.env['product.product'].search_count(
                 [('create_date', '>=', '2026-10-01'), ('create_date', '<', '2026-11-01')]))),
            ("Which products were never invoiced?",
             [step(('query_records', {'model': 'product.product', 'domain': [['id', 'in', unsold.ids + self.product_a.ids]],
                                      'related': {'mode': 'never', 'model': 'account.move.line', 'field': 'product_id'}}))],
             lambda r, m: self.assertEqual(sorted(r[0]['ids']), sorted(unsold.ids))),
            ("Show me invoice %s" % self.inv_a.name,
             [step(('get_invoice_details', {'invoice': self.inv_a.name}))],
             lambda r, m: self.assertEqual(r[0]['total'], 3000.0)),
            ("Payments received this month",
             [step(('get_payments', {'direction': 'incoming', 'period': 'mtd', 'status': 'posted'}))],
             lambda r, m: self.assertEqual(r[0]['received'], 200.0)),
            ("Unreconciled bank transactions",
             [step(('get_unreconciled_bank_lines', {'journal': '', 'limit': 10.0}))],
             lambda r, m: self.assertIn('Transfer X', [row[2] for row in r[0]['rows']])),
            ("Revenue entries above 1k this year",
             [step(('search_journal_items', {'account': revenue_code, 'min_amount': '1k', 'period': 'this year',
                                             'max_amount': 0, 'text': ''}))],
             lambda r, m: self.assertTrue(r[0]['count'] and all(max(row[6], row[7]) >= 1000 for row in r[0]['rows']))),
            ("What's our DSO?",
             [step(('get_ratios', {'period': 'ytd'}))],
             lambda r, m: self.assertIn('dso_days', r[0])),
            ("Cash forecast for the next 3 months",
             [step(('get_cash_forecast', {'granularity': 'monthly', 'periods': 3.0}))],
             lambda r, m: self.assertEqual(len(r[0]['rows']), 3)),
            ("Gross margin by product",
             [step(('get_margins', {'group_by': 'products', 'period': ''}))],
             lambda r, m: self.assertEqual(r[0]['rows'][0][0], self.product_a.display_name)),
            ("Tax report for Q3",
             [step(('get_tax_summary', {'period': 'Q3 2026'}))],
             lambda r, m: self.assertEqual(r[0]['period'], '2026-07-01..2026-09-30')),
            ("Customer invoices per month this year",
             [step(('query_records', {'model': 'account.move', 'period': 'this_year', 'date_field': 'invoice_date',
                                      'domain': [['move_type', '=', 'out_invoice'], ['state', '=', 'posted']],
                                      'group_by': 'invoice_date:monthly'}))],
             lambda r, m: self.assertEqual([row[1] for row in r[0]['rows']], [1, 2])),
            ("Total invoiced per salesperson",
             [step(('query_records', {'model': 'account.move', 'group_by': ['invoice_user_id'],
                                      'aggregate': 'sum(amount_untaxed)',
                                      'domain': '[["move_type", "=", "out_invoice"], ["state", "=", "posted"]]'}))],
             lambda r, m: self.assertEqual(sum(row[1] for row in r[0]['rows']),
                                           3000.0 + 500.0 + self.inv_b.amount_untaxed)),
            ("Balance sheet at the end of September",
             [step(('get_balance_sheet', {'date_to': '2026-09-30'}))],
             lambda r, m: self.assertEqual(r[0]['period'], '..2026-09-30')),
            ("What can I ask about partners?",
             [step(('describe_data', {'model': 'Res.Partner', 'search': 'rank'}))],
             lambda r, m: self.assertIn('customer_rank:integer', r[0]['fields'])),
            ("How did my best customer do this year vs last year?",
             [step(('get_top_partners', {'kind': 'customer', 'limit': 1})),
              step(('get_partner_summary', {'partner': self.partner_a.name, 'period': 'this year'}),
                   ('get_partner_summary', {'partner': self.partner_a.name, 'period': 'last year'}))],
             lambda r, m: (self.assertEqual(r[1]['sales'], 3400.0), self.assertEqual(r[2]['sales'], 0.0))),
        ]
        for question, steps, check in scenarios:
            with self.subTest(question=question):
                self.scenario(question, steps, check)
