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
"""Robustness of every AI tool against whatever arguments a model sends.

For each tool a realistic baseline call is mutated parameter by parameter
(types, enums, synonyms, empty and hostile values) and the output must keep
the contract the agent loop and the client rely on: no exception, no
unexpected internal failure, JSON-serialisable compact payload, well-formed
blocks, and a clear message when the call cannot be understood.

The baselines must cover every tool: a tool added without one fails
``test_every_tool_has_a_baseline``.
"""
import json
from unittest.mock import patch

from freezegun import freeze_time

from odoo import models
from odoo.tests import new_test_user, tagged
from odoo.tools import mute_logger

from .common import AiAccountingDataCommon

# Hostile or meaningless values tried on every parameter.
GARBAGE = [
    None, '', '   ', [], {}, 0, -1, 10 ** 12, 3.7, True, False, 'x' * 3000,
    "'; DROP TABLE account_move; --", '<script>alert(1)</script>', '日本語 🚀', '\x00', '%', '_',
    {'a': 1}, ['a', 'b'], [None], 'null', 'undefined', 'N/A', '[]', '{}',
]
TYPED_VARIANTS = {
    'integer': ['10', 10.0, '10.0', '5', 0, -5, 10 ** 9, '1e3', 'ten', 2.5, '1/2'],
    'number': ['1,000', '$500', '1k', 0, -1, '0.5', 'abc', 1e308],
    'boolean': ['true', 'false', 'yes', 'no', 0, 1, 'maybe'],
    'array': ['name', 'name, display_name', '["name"]', ['name', 'name'], [1, 2], [['x']]],
    'object': ['{"mode": "with"}', 'garbage', {'mode': 'sideways'}, {'model': 'res.partner'}],
}
PERIOD_VARIANTS = [
    'this_month', 'This Month', 'MTD', 'ytd', 'all', 'october', 'Oct 2026', 'Q3 2026', '2026',
    '2026-10', '2026-10-05', 'last 7 days', 'last 6 months', 'custom', 'next decade', 'blah', 42,
]
DATE_VARIANTS = ['2026-10-01', '2026-10-01T00:00:00Z', '2026-10', '01/10/2026', 'October 1, 2026',
                 '2026-13-45', 'yesterday', 20261001]
# Errors that are a correct answer to a valid-looking combination.
ACCEPTED_ERRORS = ('cannot be combined', 'No partner matches', 'No invoice matches', 'No account matches')


@tagged('post_install', '-at_install')
@freeze_time('2026-10-15')
class TestToolRobustness(AiAccountingDataCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.specs = cls.toolkit._ai_tool_specs()
        cls.baselines = {
            'get_kpi_overview': {'period': 'this_month'},
            'get_profit_and_loss': {'period': 'this_year'},
            'get_balance_sheet': {},
            'get_trial_balance': {'period': 'this_year'},
            'get_aged_balance': {'kind': 'receivable'},
            'get_top_partners': {'kind': 'customer', 'period': 'this_year'},
            'get_top_products': {'kind': 'sale', 'period': 'this_year'},
            'get_trend': {'metric': 'revenue'},
            'get_cash_balances': {},
            'get_invoices': {'kind': 'customer', 'status': 'all'},
            'get_tax_summary': {'period': 'this_year'},
            'get_partner_summary': {'partner': cls.partner_a.name},
            'get_breakdown': {'measure': 'sales', 'group_by': 'partner', 'period': 'this_year'},
            'compare_periods': {'period_a': 'this_month', 'period_b': 'last_month'},
            'get_margins': {'period': 'this_year'},
            'get_cash_forecast': {},
            'get_ratios': {},
            'get_payments': {'period': 'this_year', 'status': 'all'},
            'search_journal_items': {'period': 'this_year'},
            'get_invoice_details': {'number': cls.inv_a.name},
            'query_records': {'model': 'res.partner', 'domain': '[["customer_rank", ">", 0]]'},
            'describe_data': {'search': 'invoice'},
            'get_unreconciled_bank_lines': {},
        }

    def run_tool(self, name, arguments, context=None):
        output = self.toolkit._ai_run_tool(name, arguments)
        self.assert_tool_contract(output, context or '%s(%r)' % (name, arguments))
        return output

    def assert_ok(self, output, context):
        if output.get('error'):
            message = output['model']['error']
            self.assertTrue(any(accepted in message for accepted in ACCEPTED_ERRORS),
                            "%s failed: %s" % (context, message))

    # ------------------------------------------------------------------
    # Coverage and schemas
    # ------------------------------------------------------------------
    def test_every_tool_has_a_baseline(self):
        self.assertEqual(set(self.baselines), set(self.specs),
                         "Add a baseline call for every new tool to this robustness suite")

    def test_tool_schemas_are_valid_for_every_provider(self):
        """Names and schemas accepted by OpenAI, Anthropic and Gemini alike;
        definitions small enough to be re-sent with every request."""
        definitions = self.toolkit._ai_get_tool_definitions()
        allowed_types = {'string', 'integer', 'number', 'boolean', 'array', 'object'}

        def check(schema, path):
            self.assertIn(schema.get('type'), allowed_types, path)
            self.assertFalse(set(schema) - {'type', 'description', 'enum', 'items', 'properties'}, path)
            if 'enum' in schema:
                self.assertEqual(schema['type'], 'string', path)
                self.assertTrue(schema['enum'] and all(isinstance(value, str) for value in schema['enum']), path)
                self.assertEqual(len(schema['enum']), len(set(schema['enum'])), path)
            if schema['type'] == 'array':
                check(schema['items'], path + '[]')
            for name, child in (schema.get('properties') or {}).items():
                self.assertRegex(name, r'^[a-z][a-z0-9_]*$', path)
                check(child, '%s.%s' % (path, name))

        for definition in definitions:
            self.assertRegex(definition['name'], r'^[a-zA-Z0-9_]{1,64}$')
            self.assertTrue(definition['description'].strip())
            parameters = definition['parameters']
            self.assertEqual(parameters['type'], 'object')
            self.assertTrue(set(parameters.get('required', [])) <= set(parameters['properties']),
                            definition['name'])
            for name, schema in parameters['properties'].items():
                check(schema, '%s.%s' % (definition['name'], name))
        size = len(json.dumps(definitions, separators=(',', ':')))
        self.assertLess(size, 16000, "Tool definitions are sent with every AI call: keep them short")

    def test_baselines(self):
        for name, arguments in self.baselines.items():
            with self.subTest(tool=name):
                output = self.run_tool(name, arguments)
                self.assertFalse(output.get('error'), output['model'])
                self.assertTrue(output['digest'], name)

    # ------------------------------------------------------------------
    # Provider styles: the same question, written as each provider does
    # ------------------------------------------------------------------
    def _blank_for(self, schema):
        """What GPT models send for an optional parameter they do not use."""
        return {'string': '', 'integer': 0, 'number': 0, 'array': [], 'object': {},
                'boolean': None}[schema['type']]

    def test_gpt_style_every_optional_parameter_sent_empty(self):
        """The production failure, generalised to every tool: empty
        optional values must not change the answer."""
        for name, arguments in self.baselines.items():
            with self.subTest(tool=name):
                expected = self.run_tool(name, arguments)['model']
                padded = dict(arguments)
                for parameter, schema in self.specs[name]['parameters'].items():
                    if parameter in arguments:
                        continue
                    padded[parameter] = self._blank_for(schema)
                    if schema['type'] == 'object':
                        padded[parameter] = {key: '' for key in schema['properties']}
                        padded[parameter]['mode'] = 'without'
                output = self.run_tool(name, padded)
                self.assertFalse(output.get('error'), output['model'])
                self.assertEqual(output['model'], expected, name)

    def test_gemini_style_numbers_and_arrays(self):
        """Gemini sends integers as floats and JSON values as real arrays."""
        for name, arguments in self.baselines.items():
            parameters = self.specs[name]['parameters']
            styled = dict(arguments)
            if 'limit' in parameters:
                styled['limit'] = 10.0
            if 'periods' in parameters:
                styled['periods'] = 8.0
            if isinstance(styled.get('domain'), str):
                styled['domain'] = json.loads(styled['domain'])
            with self.subTest(tool=name):
                expected = self.run_tool(name, dict(arguments, **{
                    key: int(value) for key, value in styled.items() if isinstance(value, float)}))['model']
                output = self.run_tool(name, styled)
                self.assertFalse(output.get('error'), output['model'])
                self.assertEqual(output['model'], expected, name)

    def test_arguments_as_json_text(self):
        """Some endpoints hand over the arguments as a JSON string."""
        for name, arguments in self.baselines.items():
            with self.subTest(tool=name):
                expected = self.run_tool(name, arguments)['model']
                self.assertEqual(self.run_tool(name, json.dumps(arguments))['model'], expected)

    def test_every_enum_value_works(self):
        for name, arguments in self.baselines.items():
            for parameter, schema in self.specs[name]['parameters'].items():
                for value in schema.get('enum', []):
                    for written in (value, value.upper(), value.replace('_', ' ').title()):
                        context = '%s %s=%r' % (name, parameter, written)
                        with self.subTest(context):
                            self.assert_ok(self.run_tool(name, dict(arguments, **{parameter: written}), context),
                                           context)

    # ------------------------------------------------------------------
    # Fuzzing
    # ------------------------------------------------------------------
    def test_fuzz_every_parameter(self):
        for name, arguments in self.baselines.items():
            for parameter, schema in self.specs[name]['parameters'].items():
                values = list(GARBAGE) + TYPED_VARIANTS.get(schema['type'], [])
                if parameter.startswith('period'):
                    values += PERIOD_VARIANTS
                if parameter in ('date_from', 'date_to', 'a_from', 'a_to', 'b_from', 'b_to', 'as_of'):
                    values += DATE_VARIANTS
                for value in values:
                    context = '%s %s=%r' % (name, parameter, value if not isinstance(value, str) else value[:40])
                    with self.subTest(context):
                        self.run_tool(name, dict(arguments, **{parameter: value}), context)

    def test_fuzz_whole_arguments(self):
        shapes = [None, '', '{}', '[]', 'not json', '{"broken": ', [1, 2], 42, True,
                  {'': 1}, {'unknown_parameter': 'x'}, {'period': {'nested': True}}]
        for name in self.baselines:
            for shape in shapes:
                with self.subTest(tool=name, shape=shape):
                    self.run_tool(name, shape)

    def test_unknown_parameters_are_reported_not_ignored(self):
        for name, arguments in self.baselines.items():
            with self.subTest(tool=name):
                output = self.run_tool(name, dict(arguments, currency_code='EUR'))
                self.assertTrue(output.get('error'))
                self.assertIn('currency_code', output['model']['error'])

    def test_missing_required_parameters_are_named(self):
        for name, spec in self.specs.items():
            if not spec.get('required'):
                continue
            with self.subTest(tool=name):
                output = self.run_tool(name, {})
                self.assertTrue(output.get('error'))
                for parameter in spec['required']:
                    self.assertIn(parameter, output['model']['error'])

    def test_prefixed_and_unknown_tool_names(self):
        for written in ('default_api.get_kpi_overview', 'functions.get_kpi_overview', 'Get_KPI_Overview',
                        ' get_kpi_overview '):
            with self.subTest(written=written):
                output = self.run_tool(written, {})
                self.assertFalse(output.get('error'), output['model'])
        output = self.run_tool('get_everything', {})
        self.assertTrue(output.get('error'))
        self.assertIn('get_kpi_overview', output['model']['error'], "The error lists the real tools")

    # ------------------------------------------------------------------
    # Environments
    # ------------------------------------------------------------------
    def test_company_without_any_data(self):
        """A fresh company (chart of accounts, no entries) answers zeros,
        never a failure."""
        company = self.setup_other_company(name='AI Empty Co')['company']
        self.env.user.company_ids |= company
        toolkit = self.toolkit.with_company(company)
        for name, arguments in self.baselines.items():
            with self.subTest(tool=name):
                output = toolkit._ai_run_tool(name, arguments)
                self.assert_tool_contract(output, name)
                if name not in ('get_partner_summary', 'get_invoice_details'):
                    self.assertFalse(output.get('error'), output['model'])

    def test_user_with_limited_rights(self):
        """Tools run with the user's own access rights: missing rights give
        an error message, never a crash nor data the user cannot read."""
        for groups in ('base.group_user', 'account.group_account_invoice', 'account.group_account_readonly'):
            user = new_test_user(self.env, login='ai_limited_%s' % groups.split('.')[1], groups=groups,
                                 company_id=self.env.company.id)
            toolkit = self.toolkit.with_user(user)
            for name, arguments in self.baselines.items():
                with self.subTest(groups=groups, tool=name):
                    self.assert_tool_contract(toolkit._ai_run_tool(name, arguments), name)

    def test_tools_never_write(self):
        """V1 is read-only: no tool creates, writes or deletes a record,
        whatever the arguments."""
        def forbid(*_args, **_kwargs):
            raise AssertionError("A tool tried to write to the database")

        calls = list(self.baselines.items()) + [
            ('query_records', {'model': 'account.move', 'group_by': ['partner_id'], 'aggregate': 'amount_total:sum'}),
            ('query_records', {'model': 'product.product', 'period': 'october', 'date_field': 'create_date',
                               'related': {'mode': 'without', 'model': 'account.move.line', 'field': 'product_id'}}),
            ('get_profit_and_loss', {'compare': 'previous_year', 'detail': 'accounts', 'chart': 'bar'}),
            ('get_breakdown', {'measure': 'profit', 'group_by': 'analytic_account', 'then_by': 'month'}),
        ]
        with patch.object(models.BaseModel, 'create', forbid), \
                patch.object(models.BaseModel, 'write', forbid), \
                patch.object(models.BaseModel, 'unlink', forbid):
            with self.assertRaises(AssertionError, msg="The guard itself must work"):
                self.env['res.partner.category'].create({'name': 'Guard check'})
            for name, arguments in calls:
                with self.subTest(tool=name):
                    self.assert_tool_contract(self.toolkit._ai_run_tool(name, arguments), name)

    def test_unexpected_failure_is_contained(self):
        """A bug inside a tool is logged and reported to the AI; the
        transaction stays usable for the next tools."""
        with patch.object(type(self.toolkit), '_ai_tool_get_kpi_overview',
                          side_effect=AttributeError("boom"), autospec=True), \
                self.assertLogs('odoo.addons.ai_accounting_analytics.models.ai_accounting_toolkit',
                                level='ERROR') as logs:
            output = self.toolkit._ai_run_tool('get_kpi_overview', {})
        self.assertTrue(output['error'])
        self.assertTrue(output['internal'])
        self.assertIn('AttributeError', output['model']['error'])
        self.assertIn('get_kpi_overview', logs.output[0])
        self.assertFalse(self.toolkit._ai_run_tool('get_cash_balances', {}).get('error'))

    def test_wrong_value_types_never_reach_the_database(self):
        """Domain values are checked against the field type first, so a
        wrong value is a clear message, not a failed (and logged) query."""
        for domain, fragment in (('[["amount_total", ">", "lots"]]', 'amount_total'),
                                 ('[["id", "=", 99999999999]]', 'whole number'),
                                 ('[["id", "in", [1, "two"]]]', 'id'),
                                 ('[["invoice_date", ">=", "someday"]]', 'someday'),
                                 ('[["partner_id", "=", 1.5]]', 'whole number')):
            with self.subTest(domain=domain):
                output = self.run_tool('query_records', {'model': 'account.move', 'domain': domain})
                self.assertTrue(output.get('error'))
                self.assertIn(fragment, output['model']['error'])
        # ...and readable values of the right type work, whatever their form.
        for domain in ('[["amount_total", ">", "1,000"]]', '[["invoice_date", ">=", "2026-10-01T00:00:00Z"]]',
                       '[["create_date", ">=", "2026-10-01T00:00:00+05:30"]]', '[["partner_id", "=", "%s"]]'
                       % self.partner_a.name, '[["is_move_sent", "=", "false"]]'):
            with self.subTest(domain=domain):
                output = self.run_tool('query_records', {'model': 'account.move', 'domain': domain})
                self.assertFalse(output.get('error'), output['model'])

    def test_database_error_is_rolled_back(self):
        """Should a query still fail in PostgreSQL, only that tool call
        fails: the savepoint keeps the transaction usable."""
        def failing_query(toolkit, arguments):
            toolkit.env.cr.execute("SELECT 1 / 0")

        with patch.object(type(self.toolkit), '_ai_tool_query_records', failing_query), \
                mute_logger('odoo.sql_db'):
            output = self.toolkit._ai_run_tool('query_records', {'model': 'res.partner'})
        self.assert_tool_contract(output)
        self.assertTrue(output.get('error'))
        self.assertFalse(self.toolkit._ai_run_tool('get_cash_balances', {}).get('error'))
