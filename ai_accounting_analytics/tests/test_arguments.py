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
"""Unit tests of the tool-argument normaliser (``llm.arguments``): every
shape of argument real models were seen sending, or plausibly send."""
from datetime import date

from odoo.tests import BaseCase, tagged

from odoo.addons.ai_accounting_analytics.llm.arguments import (
    ArgumentError, check_required, normalize_arguments, parse_date, resolve_enum, resolve_period_text,
)
from odoo.addons.ai_accounting_analytics.llm.base import parse_arguments
from odoo.addons.ai_accounting_analytics.models.ai_accounting_toolkit import PERIODS

SCHEMA = {
    'properties': {
        'kind': {'type': 'string', 'enum': ['customer', 'vendor']},
        'chart': {'type': 'string', 'enum': ['none', 'bar', 'line', 'pie']},
        'limit': {'type': 'integer'},
        'min_amount': {'type': 'number'},
        'display': {'type': 'boolean'},
        'fields': {'type': 'array', 'items': {'type': 'string'}},
        'domain': {'type': 'string'},
        'partner': {'type': 'string'},
        'date_from': {'type': 'string'},
        'date_to': {'type': 'string'},
        'related': {'type': 'object', 'properties': {
            'mode': {'type': 'string', 'enum': ['with', 'without']},
            'model': {'type': 'string'}, 'field': {'type': 'string'}, 'domain': {'type': 'string'}}},
    },
    'required': ['kind'],
}
TODAY = date(2026, 10, 9)


@tagged('-at_install', 'post_install')
class TestArguments(BaseCase):

    def normalize(self, arguments):
        return normalize_arguments(SCHEMA, arguments)

    def assertArgumentError(self, arguments, *fragments):
        with self.assertRaises(ArgumentError) as caught:
            self.normalize(arguments)
        for fragment in fragments:
            self.assertIn(fragment, str(caught.exception))

    # Empty values ------------------------------------------------------
    def test_empty_values_mean_not_set(self):
        """The production failure: GPT sends every optional parameter."""
        self.assertEqual(self.normalize({
            'kind': 'customer', 'chart': '', 'limit': None, 'min_amount': '', 'fields': [],
            'domain': '   ', 'partner': '', 'related': {'mode': 'without', 'model': '', 'field': '',
                                                         'domain': ''}}),
            {'kind': 'customer'})
        self.assertEqual(self.normalize({'kind': 'vendor', 'related': {}, 'fields': ['', None]}),
                         {'kind': 'vendor'})

    def test_whole_arguments_shapes(self):
        self.assertEqual(self.normalize(None), {})
        self.assertEqual(self.normalize(''), {})
        self.assertEqual(self.normalize('{"kind": "vendor"}'), {'kind': 'vendor'})
        self.assertEqual(self.normalize('"{\\"kind\\": \\"vendor\\"}"'), {'kind': 'vendor'})
        for garbage in ('not json', '[1, 2]', 42, ['kind', 'vendor']):
            with self.subTest(garbage=garbage):
                self.assertArgumentError(garbage, 'JSON object')

    # Types ---------------------------------------------------------------
    def test_integers(self):
        for value, expected in (('10', 10), (10.0, 10), ('10.0', 10), (' 7 ', 7), ('1e2', 100), (-3, -3)):
            with self.subTest(value=value):
                self.assertEqual(self.normalize({'limit': value})['limit'], expected)
        for value in ('ten', 2.5, True, '1/2', float('nan')):
            with self.subTest(value=value):
                self.assertArgumentError({'limit': value}, 'limit')

    def test_numbers(self):
        for value, expected in (('1,250.50', 1250.5), ('$ 1,000', 1000), ('1.5k', 1500), ('2M', 2000000),
                                ('15%', 15), (99.9, 99.9), ('-20', -20)):
            with self.subTest(value=value):
                self.assertEqual(self.normalize({'min_amount': value})['min_amount'], expected)
        for value in ('abc', False, '-', 'inf'):
            with self.subTest(value=value):
                self.assertArgumentError({'min_amount': value}, 'min_amount')

    def test_booleans(self):
        for value, expected in (('false', False), ('False', False), ('no', False), (0, False),
                                ('true', True), ('YES', True), (1, True), (True, True)):
            with self.subTest(value=value):
                self.assertIs(self.normalize({'display': value})['display'], expected)
        self.assertArgumentError({'display': 'maybe'}, 'display')

    def test_strings(self):
        self.assertEqual(self.normalize({'partner': 400000})['partner'], '400000')
        self.assertEqual(self.normalize({'partner': 400000.0})['partner'], '400000')
        self.assertEqual(self.normalize({'partner': ['Azure']})['partner'], 'Azure')
        self.assertEqual(self.normalize({'partner': ' Azure\x00 '})['partner'], 'Azure')
        # A domain sent as an actual array becomes the JSON text the schema declares.
        self.assertEqual(self.normalize({'domain': [['name', '=', 'x']]})['domain'], '[["name", "=", "x"]]')

    def test_arrays(self):
        for value in ('name, email', '["name", "email"]', ('name', 'email'), ['name', ' email ', '']):
            with self.subTest(value=value):
                self.assertEqual(self.normalize({'fields': value})['fields'], ['name', 'email'])
        self.assertEqual(self.normalize({'fields': 'name'})['fields'], ['name'])

    def test_objects(self):
        related = {'mode': 'With', 'model': 'account.move.line', 'field': 'product_id'}
        self.assertEqual(self.normalize({'related': related})['related']['mode'], 'with')
        self.assertEqual(self.normalize({'related': '{"model": "account.move.line", "field": "product_id"}'}),
                         {'related': {'model': 'account.move.line', 'field': 'product_id'}})
        self.assertNotIn('related', self.normalize({'related': {'mode': 'with'}}))
        self.assertArgumentError({'related': {'modle': 'x'}}, 'modle', 'related')
        self.assertArgumentError({'related': 'garbage'}, 'related')

    # Names and enums -------------------------------------------------------
    def test_parameter_aliases(self):
        self.assertEqual(self.normalize({'type': 'vendor', 'start_date': '2026-10-01', 'end_date': '2026-10-31',
                                         'partner_name': 'Azure', 'top_n': 5, 'filters': '[]x'}),
                         {'kind': 'vendor', 'date_from': '2026-10-01', 'date_to': '2026-10-31',
                          'partner': 'Azure', 'limit': 5, 'domain': '[]x'})
        self.assertEqual(self.normalize({'Kind': 'vendor', 'Date-From': '2026-10-01'}),
                         {'kind': 'vendor', 'date_from': '2026-10-01'})
        # The declared name wins over its alias, whatever the order.
        self.assertEqual(self.normalize({'start_date': '2026-01-01', 'date_from': '2026-10-01'})['date_from'],
                         '2026-10-01')
        self.assertEqual(self.normalize({'date_from': '2026-10-01', 'start_date': '2026-01-01'})['date_from'],
                         '2026-10-01')

    def test_unknown_parameters_are_rejected(self):
        """A filter silently dropped would give a wrong figure."""
        self.assertArgumentError({'kind': 'vendor', 'currency': 'EUR'}, 'currency', 'kind, limit')
        # ...unless empty, like the other optional values.
        self.assertEqual(self.normalize({'kind': 'vendor', 'currency': ''}), {'kind': 'vendor'})

    def test_enums(self):
        for value, expected in (('Customer', 'customer'), ('CUSTOMERS', 'customer'), ('clients', 'customer'),
                                ('Suppliers', 'vendor'), ('vendor ', 'vendor')):
            with self.subTest(value=value):
                self.assertEqual(self.normalize({'kind': value})['kind'], expected)
        for value, expected in (('Column', 'bar'), ('bar chart', 'bar'), ('donut', 'pie'), ('area', 'line'),
                                ('table', 'none'), (False, 'none'), (True, 'bar')):
            with self.subTest(value=value):
                self.assertEqual(self.normalize({'chart': value})['chart'], expected)
        self.assertArgumentError({'kind': 'employee'}, 'kind must be one of: customer, vendor')

    def test_enum_synonyms_follow_the_declared_values(self):
        """One word, the right value for each parameter."""
        cases = [
            ('customers', ['sale', 'purchase'], 'sale'),
            ('customers', ['receivable', 'payable'], 'receivable'),
            ('customers', ['received', 'sent', 'all'], 'received'),
            ('vendors', ['received', 'sent', 'all'], 'sent'),
            ('customers', ['partner', 'product', 'month'], 'partner'),
            ('sales', ['sales', 'purchases', 'revenue'], 'sales'),
            ('sales', ['amount', 'quantity'], 'amount'),
            ('qty', ['amount', 'quantity'], 'quantity'),
            ('unpaid', ['open', 'overdue', 'paid', 'draft', 'all'], 'open'),
            ('late', ['open', 'overdue', 'paid', 'draft', 'all'], 'overdue'),
            ('posted', ['open', 'overdue', 'paid', 'draft', 'all'], 'all'),
            ('posted', ['done', 'draft', 'all'], 'done'),
            ('paid', ['done', 'draft', 'all'], 'done'),
            ('monthly', ['day', 'week', 'month', 'quarter', 'year'], 'month'),
            ('yearly', ['day', 'week', 'month', 'quarter', 'year'], 'year'),
            ('category', ['partner', 'product', 'product_category'], 'product_category'),
            ('yoy', ['none', 'previous_period', 'previous_year'], 'previous_year'),
            ('last month', ['none', 'previous_period', 'previous_year'], 'previous_period'),
            ('detailed', ['summary', 'accounts'], 'accounts'),
            ('never', ['with', 'without'], 'without'),
            ('largest', ['amount_desc', 'date_desc', 'due_asc'], 'amount_desc'),
        ]
        for value, allowed, expected in cases:
            with self.subTest(value=value, allowed=allowed):
                self.assertEqual(resolve_enum(value, allowed, 'x'), expected)

    def test_required(self):
        check_required(SCHEMA, {'kind': 'vendor'})
        with self.assertRaises(ArgumentError) as caught:
            check_required(SCHEMA, {'kind': ''})
        self.assertIn('kind (customer | vendor)', str(caught.exception))

    # Dates and periods ---------------------------------------------------
    def test_dates(self):
        cases = [
            ('2026-10-05', date(2026, 10, 5), date(2026, 10, 5)),
            ('2026-10-05T00:00:00Z', date(2026, 10, 5), date(2026, 10, 5)),
            ('2026-10-05 13:45:00', date(2026, 10, 5), date(2026, 10, 5)),
            ('2026/10/5', date(2026, 10, 5), date(2026, 10, 5)),
            ('20261005', date(2026, 10, 5), date(2026, 10, 5)),
            (20261005, date(2026, 10, 5), date(2026, 10, 5)),
            ('2026-10', date(2026, 10, 1), date(2026, 10, 31)),
            ('2026-02', date(2026, 2, 1), date(2026, 2, 28)),
            ('2026', date(2026, 1, 1), date(2026, 12, 31)),
            ('October 5, 2026', date(2026, 10, 5), date(2026, 10, 5)),
            ('5 Oct 2026', date(2026, 10, 5), date(2026, 10, 5)),
            ('October 2026', date(2026, 10, 1), date(2026, 10, 31)),
            (date(2026, 10, 5), date(2026, 10, 5), date(2026, 10, 5)),
        ]
        for value, start, end in cases:
            with self.subTest(value=value):
                self.assertEqual(parse_date(value), start)
                self.assertEqual(parse_date(value, end=True), end)
        self.assertEqual(parse_date('05/10/2026', dayfirst=True), date(2026, 10, 5))
        self.assertEqual(parse_date('10/05/2026', dayfirst=False), date(2026, 10, 5))
        for value in ('not a date', '2026-13-01', '2026-02-30', '', None, 'Oct 5', True):
            with self.subTest(value=value), self.assertRaises(ArgumentError):
                parse_date(value)

    def test_periods_in_words(self):
        cases = [
            ('this_month', ('this_month', None, None)),
            ('This Month', ('this_month', None, None)),
            ('current-month', ('this_month', None, None)),
            ('MTD', ('this_month', None, None)),
            ('YTD', ('year_to_date', None, None)),
            ('previous year', ('last_year', None, None)),
            ('last fiscal year', ('last_year', None, None)),
            ('all', ('all_time', None, None)),
            ('TTM', ('last_12_months', None, None)),
            ('last week', ('last_week', None, None)),
            ('last 12 months', ('last_12_months', None, None)),
            ('october', ('custom', date(2026, 10, 1), date(2026, 10, 31))),
            ('Oct 2026', ('custom', date(2026, 10, 1), date(2026, 10, 31))),
            ('october_2025', ('custom', date(2025, 10, 1), date(2025, 10, 31))),
            ('2026 october', ('custom', date(2026, 10, 1), date(2026, 10, 31))),
            # A month still to come this year means last year's.
            ('November', ('custom', date(2025, 11, 1), date(2025, 11, 30))),
            ('sept', ('custom', date(2026, 9, 1), date(2026, 9, 30))),
            ('Q3 2026', ('custom', date(2026, 7, 1), date(2026, 9, 30))),
            ('2026-Q1', ('custom', date(2026, 1, 1), date(2026, 3, 31))),
            ('q4', ('custom', date(2026, 10, 1), date(2026, 12, 31))),
            ('2025', ('custom', date(2025, 1, 1), date(2025, 12, 31))),
            ('FY2025', ('custom', date(2025, 1, 1), date(2025, 12, 31))),
            ('2026-10', ('custom', date(2026, 10, 1), date(2026, 10, 31))),
            ('2026-10-05', ('custom', date(2026, 10, 5), date(2026, 10, 5))),
            ('last 7 days', ('custom', date(2026, 10, 3), date(2026, 10, 9))),
            ('past thirty days', ('custom', date(2026, 9, 10), date(2026, 10, 9))),
            ('last 2 weeks', ('custom', date(2026, 9, 26), date(2026, 10, 9))),
            ('last 6 months', ('custom', date(2026, 5, 1), date(2026, 10, 9))),
            ('last 2 quarters', ('custom', date(2026, 5, 1), date(2026, 10, 9))),
            ('last 2 years', ('custom', date(2024, 10, 10), date(2026, 10, 9))),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(resolve_period_text(value, TODAY, PERIODS), expected)
        for value in ('blah', 'next month', 'q5', 'the day after'):
            with self.subTest(value=value), self.assertRaises(ArgumentError) as caught:
                resolve_period_text(value, TODAY, PERIODS)
            self.assertIn('this_month', str(caught.exception))

    # Raw tool-call arguments ---------------------------------------------
    def test_parse_arguments(self):
        cases = [
            ('{"a": 1}', ({'a': 1}, True)),
            ({'a': 1}, ({'a': 1}, True)),
            ('', ({}, True)),
            ('  ', ({}, True)),
            (None, ({}, True)),
            ('null', ({}, True)),
            ('"{\\"a\\": 1}"', ({'a': 1}, True)),
            ("{'a': 1, 'b': True}", ({'a': 1, 'b': True}, True)),
            ('{"a": 1', ({}, False)),
            ('[1, 2]', ({}, False)),
            ('{"a": 1}{"b": 2}', ({}, False)),
            (42, ({}, False)),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(parse_arguments(raw), expected)
