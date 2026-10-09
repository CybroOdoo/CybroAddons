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
"""The way a model writes a call must not change the answer.

Each case pairs a call written the way models actually write it (synonyms,
other parameter names, periods in words, other date formats, other domain
syntaxes) with the documented call; both must return exactly the same data.
Fuzzing proves nothing crashes; these prove nothing is silently misread
(e.g. "customers" read as vendors, or dates ignored).
"""
import json

from freezegun import freeze_time

from odoo.tests import tagged

from .common import AiAccountingDataCommon


@tagged('post_install', '-at_install')
@freeze_time('2026-10-15')
class TestToolSemantics(AiAccountingDataCommon):

    def run_tool(self, name, arguments):
        output = self.toolkit._ai_run_tool(name, arguments)
        self.assert_tool_contract(output, name)
        self.assertFalse(output.get('error'), '%s(%r): %s' % (name, arguments, output['model']))
        return output

    def assertSameAnswer(self, name, written, documented):
        self.assertEqual(self.run_tool(name, written)['model'], self.run_tool(name, documented)['model'],
                         '%s: %r should mean %r' % (name, written, documented))

    def assertError(self, name, arguments, *fragments):
        output = self.toolkit._ai_run_tool(name, arguments)
        self.assert_tool_contract(output, name)
        self.assertTrue(output.get('error'), '%s(%r) should fail' % (name, arguments))
        for fragment in fragments:
            self.assertIn(fragment, output['model']['error'])
        return output['model']['error']

    def test_equivalent_calls(self):
        october = {'period': 'custom', 'date_from': '2026-10-01', 'date_to': '2026-10-31'}
        revenue_code = self.company_data['default_account_revenue'].code
        cases = [
            # enum synonyms, case and plural forms
            ('get_top_partners', {'kind': 'Customers'}, {'kind': 'customer'}),
            ('get_top_partners', {'kind': 'suppliers'}, {'kind': 'vendor'}),
            ('get_top_partners', {'type': 'client'}, {'kind': 'customer'}),
            ('get_top_products', {'kind': 'sales', 'metric': 'qty'}, {'kind': 'sale', 'metric': 'quantity'}),
            ('get_invoices', {'kind': 'customer', 'status': 'unpaid'}, {'kind': 'customer', 'status': 'open'}),
            ('get_invoices', {'type': 'customers', 'status': 'late', 'order': 'largest'},
             {'kind': 'customer', 'status': 'overdue', 'order': 'amount_desc'}),
            ('get_invoices', {'kind': 'bills', 'status': 'posted'}, {'kind': 'vendor', 'status': 'all'}),
            ('get_aged_balance', {'kind': 'customers'}, {'kind': 'receivable'}),
            ('get_aged_balance', {'kind': 'AP'}, {'kind': 'payable'}),
            ('get_payments', {'kind': 'inbound', 'status': 'posted', 'period': 'this_year'},
             {'kind': 'received', 'status': 'done', 'period': 'this_year'}),
            ('get_breakdown', {'measure': 'Sales', 'group_by': 'customers', 'then_by': 'monthly', 'period': 'ytd'},
             {'measure': 'sales', 'group_by': 'partner', 'then_by': 'month', 'period': 'year_to_date'}),
            ('get_breakdown', {'metric': 'income', 'dimension': 'category'},
             {'measure': 'revenue', 'group_by': 'product_category'}),
            ('get_trend', {'metric': 'Revenue', 'granularity': 'Monthly', 'chart': 'column'},
             {'metric': 'revenue', 'granularity': 'month', 'chart': 'bar'}),
            ('get_profit_and_loss', {'compare': 'yoy', 'detail': 'detailed'},
             {'compare': 'previous_year', 'detail': 'accounts'}),
            ('get_cash_forecast', {'granularity': 'monthly', 'periods': '6'}, {'granularity': 'month', 'periods': 6}),
            ('get_margins', {'group_by': 'partners'}, {'group_by': 'customer'}),
            # periods in words and dates in other formats
            ('get_top_partners', {'kind': 'customer', 'period': 'October'}, dict(october, kind='customer')),
            ('get_top_partners', {'kind': 'customer', 'period': 'Oct 2026'}, dict(october, kind='customer')),
            ('get_top_partners', {'kind': 'customer', 'period': '2026-10'}, dict(october, kind='customer')),
            ('get_top_partners', {'kind': 'customer', 'period': 'This Month'},
             {'kind': 'customer', 'period': 'this_month'}),
            ('get_top_partners', {'kind': 'customer', 'period': 'MTD'}, {'kind': 'customer', 'period': 'this_month'}),
            ('get_top_partners', {'kind': 'customer', 'period': 'Q4'},
             {'kind': 'customer', 'period': 'custom', 'date_from': '2026-10-01', 'date_to': '2026-12-31'}),
            ('get_top_partners', {'kind': 'customer', 'start_date': '2026-10-01', 'end_date': '2026-10-31'},
             dict(october, kind='customer')),
            # Dates without period=custom are a custom period, never ignored.
            ('get_top_partners', {'kind': 'customer', 'date_from': '2026-10-01', 'date_to': '2026-10-31'},
             dict(october, kind='customer')),
            ('get_top_partners', {'kind': 'customer', 'period': 'this_year', 'date_from': '2026-10-01',
                                  'date_to': '2026-10-31'}, dict(october, kind='customer')),
            ('get_top_partners', {'kind': 'customer', 'period': 'custom', 'date_from': '2026-10-31',
                                  'date_to': '2026-10-01'}, dict(october, kind='customer')),
            ('get_top_partners', {'kind': 'customer', 'period': 'custom', 'date_from': '2026-10-01T00:00:00Z',
                                  'date_to': '2026-10-31T23:59:59Z'}, dict(october, kind='customer')),
            ('get_top_partners', {'kind': 'customer', 'period': 'custom', 'date_from': 'October 1, 2026',
                                  'date_to': '2026-10'}, dict(october, kind='customer')),
            ('compare_periods', {'period_a': 'October 2026', 'period_b': 'September 2026'},
             {'period_a': 'custom', 'a_from': '2026-10-01', 'a_to': '2026-10-31',
              'period_b': 'custom', 'b_from': '2026-09-01', 'b_to': '2026-09-30'}),
            ('compare_periods', {'a_from': '2026-10-01', 'a_to': '2026-10-31', 'period_b': 'last month'},
             {'period_a': 'custom', 'a_from': '2026-10-01', 'a_to': '2026-10-31', 'period_b': 'last_month'}),
            ('get_aged_balance', {'kind': 'receivable', 'as_of': '2026-10-15T00:00:00'},
             {'kind': 'receivable', 'as_of': '2026-10-15'}),
            ('get_aged_balance', {'kind': 'receivable', 'as_of': '2026-09'},
             {'kind': 'receivable', 'as_of': '2026-09-30'}),
            # other value types and parameter names
            ('search_journal_items', {'account': int(revenue_code) if revenue_code.isdigit() else revenue_code,
                                      'period': 'this_year'},
             {'account': revenue_code, 'period': 'this_year'}),
            ('search_journal_items', {'min_amount': '1,000', 'max_amount': 0, 'period': 'this_year'},
             {'min_amount': 1000, 'period': 'this_year'}),
            ('get_invoice_details', {'invoice_number': self.inv_a.name}, {'number': self.inv_a.name}),
            ('get_partner_summary', {'customer': self.partner_a.name}, {'partner': self.partner_a.name}),
            ('get_top_partners', {'kind': 'customer', 'limit': '3'}, {'kind': 'customer', 'limit': 3}),
            ('get_top_partners', {'kind': 'customer', 'top_n': 3.0}, {'kind': 'customer', 'limit': 3}),
        ]
        for name, written, documented in cases:
            with self.subTest(tool=name, written=written):
                self.assertSameAnswer(name, written, documented)

    def test_equivalent_queries(self):
        customers = '[["customer_rank", ">", 0]]'
        moves = (self.inv_a + self.inv_b + self.inv_sep).ids
        cases = [
            # domain as an array, a Python literal, a single condition, operator aliases
            ({'model': 'res.partner', 'domain': [['customer_rank', '>', 0]]}, {'model': 'res.partner', 'domain': customers}),
            ({'model': 'res.partner', 'domain': "[('customer_rank', '>', 0)]"},
             {'model': 'res.partner', 'domain': customers}),
            ({'model': 'res.partner', 'domain': '["customer_rank", ">", 0]'}, {'model': 'res.partner', 'domain': customers}),
            ({'model': 'res.partner', 'domain': '[["customer_rank", "gt", 0]]'},
             {'model': 'res.partner', 'domain': customers}),
            ({'model': 'res.partner', 'domain': '[["customer_rank", ">", "0"]]'},
             {'model': 'res.partner', 'domain': customers}),
            ({'model_name': 'res.partner', 'filters': customers}, {'model': 'res.partner', 'domain': customers}),
            ({'model': 'account.move', 'domain': json.dumps([['id', 'in', moves], ['move_type', '==', 'out_invoice']])},
             {'model': 'account.move', 'domain': json.dumps([['id', 'in', moves], ['move_type', '=', 'out_invoice']])}),
            ({'model': 'account.move', 'domain': json.dumps([['id', 'in', moves], ['name', 'contains', 'INV']])},
             {'model': 'account.move', 'domain': json.dumps([['id', 'in', moves], ['name', 'ilike', 'INV']])}),
            # fields and group_by as text
            ({'model': 'res.partner', 'domain': customers, 'fields': 'name, email'},
             {'model': 'res.partner', 'domain': customers, 'fields': ['name', 'email']}),
            ({'model': 'account.move', 'domain': json.dumps([['id', 'in', moves]]), 'group_by': 'partner_id',
              'aggregate': 'sum(amount_total)'},
             {'model': 'account.move', 'domain': json.dumps([['id', 'in', moves]]), 'group_by': ['partner_id'],
              'aggregate': 'amount_total:sum'}),
            ({'model': 'account.move', 'domain': json.dumps([['id', 'in', moves]]), 'group_by': ['partner_id'],
              'aggregate': 'sum:amount_total'},
             {'model': 'account.move', 'domain': json.dumps([['id', 'in', moves]]), 'group_by': ['partner_id'],
              'aggregate': 'amount_total:sum'}),
            ({'model': 'account.move', 'domain': json.dumps([['id', 'in', moves]]), 'group_by': ['partner_id'],
              'aggregate': 'amount_total:total'},
             {'model': 'account.move', 'domain': json.dumps([['id', 'in', moves]]), 'group_by': ['partner_id'],
              'aggregate': 'amount_total:sum'}),
            ({'model': 'account.move', 'domain': json.dumps([['id', 'in', moves]]), 'group_by': ['partner_id'],
              'aggregate': 'COUNT(*)'},
             {'model': 'account.move', 'domain': json.dumps([['id', 'in', moves]]), 'group_by': ['partner_id']}),
            ({'model': 'account.move', 'domain': json.dumps([['id', 'in', moves]]), 'group_by': ['invoice_date:monthly']},
             {'model': 'account.move', 'domain': json.dumps([['id', 'in', moves]]), 'group_by': ['invoice_date:month']}),
            ({'model': 'account.move', 'domain': json.dumps([['id', 'in', moves]]), 'group_by': ['invoice_date']},
             {'model': 'account.move', 'domain': json.dumps([['id', 'in', moves]]), 'group_by': ['invoice_date:month']}),
            # related filter: mode synonyms, object as text
            ({'model': 'product.product', 'related': '{"mode": "never", "model": "account.move.line", '
                                                     '"field": "product_id"}'},
             {'model': 'product.product', 'related': {'mode': 'without', 'model': 'account.move.line',
                                                      'field': 'product_id'}}),
            ({'model': 'res.partner', 'display': 'false', 'domain': customers},
             {'model': 'res.partner', 'display': False, 'domain': customers}),
        ]
        for written, documented in cases:
            with self.subTest(written=written):
                self.assertSameAnswer('query_records', written, documented)

    def test_synonyms_are_not_confused(self):
        """The bug class this guards: any value other than 'customer' used
        to be read as vendors."""
        customers = self.run_tool('get_top_partners', {'kind': 'customers', 'period': 'this_year'})['model']
        vendors = self.run_tool('get_top_partners', {'kind': 'vendors', 'period': 'this_year'})['model']
        self.assertEqual(customers['total'], 3000.0 + 1000.0 + 500.0 - 100.0)
        self.assertEqual(vendors['total'], 400.0)
        self.assertError('get_top_partners', {'kind': 'employees'}, 'customer, vendor')

    def test_products_created_in_october(self):
        """The production question, in every form a model may write it."""
        october = self.env['product.product'].create([{'name': 'AI Oct %s' % index} for index in range(3)])
        september = self.env['product.product'].create({'name': 'AI Sep'})
        self.env.cr.execute("UPDATE product_product SET create_date = '2026-10-31 20:00:00' WHERE id IN %s",
                            [tuple(october.ids)])
        self.env.cr.execute("UPDATE product_product SET create_date = '2026-09-30 10:00:00' WHERE id = %s",
                            [september.id])
        (october + september).invalidate_recordset(['create_date'])
        self.env.user.tz = 'UTC'
        scope = json.dumps([['id', 'in', (october + september).ids]])
        expected = sorted(october.ids)
        calls = [
            {'period': 'custom', 'date_from': '2026-10-01', 'date_to': '2026-10-31', 'date_field': 'create_date'},
            {'period': 'october', 'date_field': 'create_date'},
            {'period': 'Oct 2026', 'date_field': 'create_date'},
            {'period': 'this_month', 'date_field': 'create_date'},
            {'date_from': '2026-10-01', 'date_to': '2026-10-31', 'date_field': 'create_date'},
            {'start_date': '2026-10-01', 'end_date': '2026-10-31', 'date_field': 'create_date'},
            # date conditions written in the domain itself
            {'domain_extra': [['create_date', '>=', '2026-10-01'], ['create_date', '<', '2026-11-01']]},
            {'domain_extra': [['create_date', '>=', '2026-10-01T00:00:00Z'],
                              ['create_date', '<=', '2026-10-31T23:59:59Z']]},
            # GPT style: every optional parameter sent, empty
            {'period': 'october', 'date_field': 'create_date', 'fields': ['id'], 'group_by': [], 'order': '',
             'aggregate': 'count', 'display': False, 'chart': 'none', 'limit': 10,
             'related': {'mode': 'without', 'field': '', 'model': '', 'domain': ''}},
        ]
        for call in calls:
            with self.subTest(call=call):
                arguments = {'model': 'product.product', 'domain': scope, **call}
                if 'domain_extra' in call:
                    arguments['domain'] = json.dumps(json.loads(scope) + arguments.pop('domain_extra'))
                model = self.run_tool('query_records', arguments)['model']
                self.assertEqual(model['count'], 3)
                self.assertEqual(sorted(model['ids']), expected)

    def test_clear_errors(self):
        """When a call cannot be understood, the message says what to send."""
        self.assertError('get_top_partners', {'kind': 'customer', 'period': 'someday'},
                         'Unknown period', 'this_month', 'custom')
        self.assertError('get_top_partners', {'kind': 'customer', 'period': 'custom'}, 'date_from')
        self.assertError('get_top_partners', {'kind': 'customer', 'period': 'custom', 'date_from': '31/31/2026'},
                         'YYYY-MM-DD')
        self.assertError('get_top_partners', {'kind': 'customer', 'colour': 'red'}, 'colour', 'Parameters')
        self.assertError('get_top_partners', {}, 'kind (customer | vendor)')
        self.assertError('get_breakdown', {'measure': 'sales', 'group_by': 'weather'}, 'group_by must be one of')
        self.assertError('query_records', {'model': 'res.partner', 'domain': 'customers please'}, 'not valid JSON')
        self.assertError('query_records', {'model': 'res.partner', 'domain': '[["name", "~", "x"]]'},
                         'not allowed', 'ilike')
        self.assertError('query_records', {'model': 'res.partner', 'group_by': ['name:month']}, 'not a date field')
        self.assertError('query_records', {'model': 'res.partner', 'group_by': ['name'], 'aggregate': 'name:sum'},
                         'not numeric')
        self.assertError('query_records', {'model': 'res.partner', 'aggregate': 'sum'}, 'amount_total:sum')

    def test_query_security_cannot_be_bypassed(self):
        """Odd syntaxes must not open a way around the field and record
        checks."""
        self.assertError('query_records', {'model': 'res.partner', 'domain': '[["child_ids", "any!", []]]'},
                         'not allowed')
        self.assertError('query_records', {'model': 'res.partner',
                                           'domain': '[["user_ids", "any", [["password", "!=", false]]]]'},
                         'password')
        self.assertError('query_records', {'model': 'res.partner',
                                           'domain': '[["user_ids", "any", "[[\\"api_key_ids\\", \\"!=\\", false]]"]]'},
                         'api_key_ids')
        self.assertError('query_records', {'model': 'res.partner',
                                           'domain': '[["user_ids", "any", [["login", "=", "admin"]]]]'},
                         'res.users')
        self.assertError('query_records', {'model': 'res.partner', 'domain': '[["user_ids.login", "=", "admin"]]'},
                         'res.users')
        self.assertError('query_records', {'model': 'res.partner', 'fields': ['name'],
                                           'group_by': ['user_ids.login']}, 'res.users')
        self.assertError('query_records', {'model': 'res.partner', 'order': 'signup_token desc'}, 'signup_token')
        self.assertError('query_records', {'model': 'res.partner', 'group_by': ['user_ids.password']}, 'password')
        self.assertError('query_records', {'model': 'res.partner', 'aggregate': 'password:count_distinct',
                                           'group_by': ['name']}, 'password')
        self.assertError('query_records', {'model': ' Res.Users '}, 'not available')
        self.assertError('query_records', {'model': 'ir.config_parameter'}, 'not available')
        self.assertError('query_records', {'model': 'product.product', 'related': {
            'model': 'res.users', 'field': 'partner_id'}}, 'not available')
        self.assertError('describe_data', {'model': 'res.users'}, 'not available')
        # Pointing to a user stays possible: invoices by salesperson.
        output = self.run_tool('query_records', {'model': 'account.move', 'group_by': ['invoice_user_id']})
        self.assertTrue(output['model']['rows'])
