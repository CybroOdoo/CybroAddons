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

from odoo.tests import tagged

from .common import AiAccountingCommon


@tagged('post_install', '-at_install')
@freeze_time('2026-10-15')
class TestTools(AiAccountingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.inv_a = cls._invoice('out_invoice', cls.partner_a, '2026-10-05', 3000.0, '2026-10-10')
        cls.inv_b = cls._invoice('out_invoice', cls.partner_b, '2026-10-06', 1000.0, '2026-11-30')
        cls.bill = cls._invoice('in_invoice', cls.partner_b, '2026-10-07', 400.0, '2026-11-30')
        cls.old_invoice = cls._invoice('out_invoice', cls.partner_a, '2026-09-10', 500.0, '2026-09-10')

    @classmethod
    def _invoice(cls, move_type, partner, invoice_date, amount, due_date):
        move = cls.init_invoice(move_type, partner, invoice_date, amounts=[amount], taxes=[])
        move.write({'invoice_payment_term_id': False, 'invoice_date_due': due_date})
        move.action_post()
        return move

    def run_tool(self, name, **arguments):
        output = self.toolkit._ai_run_tool(name, arguments)
        self.assertFalse(output.get('error'), output['model'])
        return output

    def test_tool_definitions_are_stable(self):
        definitions = self.toolkit._ai_get_tool_definitions()
        names = [definition['name'] for definition in definitions]
        self.assertEqual(names, sorted(names), "Sorted for a byte-stable cached prefix")
        for definition in definitions:
            self.assertEqual(definition['parameters']['type'], 'object')
            self.assertTrue(definition['description'])
            self.assertTrue(hasattr(self.toolkit, '_ai_tool_%s' % definition['name']))

    def test_top_customers(self):
        output = self.run_tool('get_top_partners', kind='customer', period='this_month', chart='bar')
        rows = output['model']['rows']
        self.assertEqual(rows[0][0], self.partner_a.display_name)
        self.assertEqual(rows[0][2], 3000.0)
        self.assertEqual(rows[1][2], 1000.0)
        self.assertEqual(output['model']['total'], 4000.0)
        self.assertEqual([block['type'] for block in output['blocks']], ['table', 'chart'])
        self.assertIn(self.partner_a.display_name, output['digest'])

    def test_top_vendors_positive_amounts(self):
        output = self.run_tool('get_top_partners', kind='vendor', period='this_month')
        self.assertEqual(output['model']['rows'][0][2], 400.0)

    def test_kpi_overview(self):
        output = self.run_tool('get_kpi_overview', period='this_month')
        model = output['model']
        self.assertEqual(model['revenue'], 4000.0)
        self.assertEqual(model['revenue_prev'], 500.0)
        self.assertEqual(model['expenses'], 400.0)
        self.assertEqual(model['net_profit'], 3600.0)
        self.assertEqual(model['overdue_receivables'], 3500.0)
        self.assertEqual(model['receivables'], 4500.0)
        self.assertEqual(output['blocks'][0]['type'], 'kpis')

    def test_profit_and_loss(self):
        output = self.run_tool('get_profit_and_loss', period='this_month', compare='previous_period')
        lines = {row[0]: row for row in output['model']['rows']}
        self.assertEqual(lines['Profit and Loss'][1], 3600.0)
        self.assertEqual(lines['Profit and Loss'][2], 500.0)
        table = output['blocks'][0]
        self.assertEqual(table['export']['model'], 'financial.report')
        self.assertEqual(len(table['columns']), 4)

    def test_balance_sheet_and_trial_balance(self):
        output = self.run_tool('get_balance_sheet')
        self.assertTrue(output['model']['rows'])
        output = self.run_tool('get_trial_balance', period='this_month')
        debit, credit, _balance = output['model']['totals']
        self.assertAlmostEqual(debit, credit)

    def test_aged_receivable(self):
        output = self.run_tool('get_aged_balance', kind='receivable')
        model = output['model']
        self.assertEqual(model['totals'][-1], 4500.0)
        self.assertEqual(len(model['cols']), 8)

    def test_invoices_overdue(self):
        output = self.run_tool('get_invoices', kind='customer', status='overdue')
        model = output['model']
        numbers = [row[0] for row in model['rows']]
        self.assertEqual(model['count'], 2)
        self.assertIn(self.inv_a.name, numbers)
        self.assertIn(self.old_invoice.name, numbers)
        self.assertNotIn(self.inv_b.name, numbers)
        self.assertEqual(model['amount_due'], 3500.0)
        rows = output['blocks'][0]['rows']
        self.assertIn(('account.move', self.inv_a.id), [(r['res_model'], r['res_id']) for r in rows])

    def test_trend_fills_gaps(self):
        output = self.run_tool('get_trend', metric='sales', period='last_12_months')
        self.assertEqual(len(output['blocks'][0]['labels']), 12)
        self.assertEqual(output['model']['rows'][-1][1], 4000.0)
        self.assertEqual(output['model']['rows'][-2][1], 500.0)

    def test_cash_and_tax(self):
        self.run_tool('get_cash_balances')
        output = self.run_tool('get_tax_summary', period='this_month')
        self.assertIn('net_tax', output['model'])

    def test_partner_summary(self):
        output = self.run_tool('get_partner_summary', partner=self.partner_a.name)
        self.assertEqual(output['model']['receivable'], 3500.0)
        self.assertEqual(output['model']['overdue'], 3500.0)
        self.env['res.partner'].create({'name': '%s Twin' % self.partner_a.name})
        output = self.run_tool('get_partner_summary', partner=self.partner_a.name[:-1])
        self.assertTrue(output['model']['ambiguous'])

    def test_model_payload_is_row_limited(self):
        self.env['ir.config_parameter'].sudo().set_int('ai_accounting_analytics.model_rows', 1)
        output = self.run_tool('get_top_partners', kind='customer', period='this_month')
        self.assertEqual(len(output['model']['rows']), 1)
        self.assertEqual(output['model']['more_rows'], 1)
        self.assertEqual(len(output['blocks'][0]['rows']), 2, "The user still sees every row")

    def test_errors_are_returned_to_the_model(self):
        output = self.toolkit._ai_run_tool('drop_database', {})
        self.assertTrue(output['error'])
        output = self.toolkit._ai_run_tool('get_trial_balance', {'period': 'custom',
                                                                 'date_from': 'yesterday'})
        self.assertTrue(output['error'])
        self.assertIn('YYYY-MM-DD', output['model']['error'])
