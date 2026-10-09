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
import json
import logging
import re
import time
from collections import defaultdict
from datetime import datetime, time as dt_time, timedelta
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta
from psycopg2 import Error as PsycopgError

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Domain
from odoo.tools import date_utils
from odoo.tools.misc import format_date

from ..llm.arguments import (
    ArgumentError, check_required, coerce_boolean, coerce_number, normalize_arguments, normalize_key,
    parse_date, parse_json, resolve_enum, resolve_period_text,
)

_logger = logging.getLogger(__name__)

PERIODS = [
    'today', 'yesterday', 'this_week', 'last_week', 'this_month', 'last_month',
    'this_quarter', 'last_quarter', 'this_year', 'last_year', 'year_to_date',
    'last_30_days', 'last_90_days', 'last_12_months', 'all_time', 'custom',
]
INCOME_TYPES = ('income', 'income_other')
EXPENSE_TYPES = ('expense', 'expense_depreciation', 'expense_direct_cost')
CUSTOMER_MOVE_TYPES = ('out_invoice', 'out_refund')
VENDOR_MOVE_TYPES = ('in_invoice', 'in_refund')
MAX_ROWS = 50
TIME_DIMENSIONS = ('day', 'week', 'month', 'quarter', 'year')
# Generic queries: technical and security models are never reachable, and
# fields whose name looks like a secret are never read nor filtered on.
DENIED_MODEL_PREFIXES = (
    'ir.', 'res.users', 'res.groups', 'res.config', 'res.device', 'base.', 'base_import.', 'bus.',
    'mail.', 'auth', 'iap.', 'ai.accounting.', 'payment.provider', 'payment.token', 'fetchmail.',
    'web_editor.', 'html_editor.', 'publisher_warranty.', 'digest.', 'sms.', 'spreadsheet',
    'onboarding.', 'change.password', 'account.edi.proxy',
)
SECRET_FIELD_MARKERS = ('password', 'passwd', 'token', 'secret', 'api_key', 'apikey', 'signature',
                        'totp', 'oauth', 'private_key', 'credential')
QUERY_AGGREGATES = ('sum', 'avg', 'min', 'max', 'count_distinct')
AGGREGATE_ALIASES = {'average': 'avg', 'mean': 'avg', 'total': 'sum', 'minimum': 'min',
                     'maximum': 'max', 'distinct': 'count_distinct', 'unique': 'count_distinct',
                     'count': 'count_distinct'}
# Domain operators accepted from the AI. "any!" is left out on purpose: it
# skips the record rules of the related model.
DOMAIN_OPERATORS = ('=', '!=', '>', '>=', '<', '<=', 'in', 'not in', 'like', 'not like', 'ilike',
                    'not ilike', '=like', 'not =like', '=ilike', 'not =ilike', 'child_of', 'parent_of',
                    'any', 'not any')
OPERATOR_ALIASES = {'==': '=', 'eq': '=', 'is': '=', 'equals': '=', '<>': '!=', 'ne': '!=',
                    'neq': '!=', 'is not': '!=', 'is_not': '!=', 'not': '!=', 'gt': '>', 'gte': '>=',
                    'ge': '>=', '=>': '>=', 'lt': '<', 'lte': '<=', 'le': '<=', '=<': '<=',
                    'contains': 'ilike', 'icontains': 'ilike', 'not contains': 'not ilike',
                    'not_contains': 'not ilike', 'not_in': 'not in', 'nin': 'not in', 'notin': 'not in',
                    'not_ilike': 'not ilike', 'not_like': 'not like', 'iequals': '=ilike',
                    'in_list': 'in', 'not_any': 'not any'}
MAX_DOMAIN_ITEMS = 30
MAX_INTEGER = 2 ** 31 - 1
# Sizes of what a tool returns besides its data (error messages may quote
# whatever the model sent).
MAX_ERROR_LENGTH = 500
MAX_LABEL_LENGTH = 200
MAX_DIGEST_LENGTH = 600
# Returned with every failed generic query so the AI can fix its call in
# one more step instead of guessing.
QUERY_HINT = (
    'domain is a JSON list of [field, operator, value] (operators: = != > >= < <= in "not in" '
    'ilike "not ilike" =like); record ids are integers from the "ids"/"group_ids" of earlier results; '
    'use describe_data for field names; for records with or without related records use the '
    '"related" parameter instead of copying ids; for date filters use period + date_field.')
MAX_QUERY_FIELDS = 8
# Breakdown dimensions: groupby path on account.move.line (related many2one
# paths are grouped in SQL by the ORM).
BREAKDOWN_DIMENSIONS = {
    'partner': 'partner_id',
    'product': 'product_id',
    'product_category': 'product_id.categ_id',
    'account': 'account_id',
    'journal': 'journal_id',
    'country': 'partner_id.country_id',
    'salesperson': 'move_id.invoice_user_id',
}
# Measure -> (extra domain on account.move.line, sign applied to balance).
BREAKDOWN_MEASURES = {
    'sales': ([('move_id.move_type', 'in', ('out_invoice', 'out_refund')),
               ('display_type', '=', 'product')], -1),
    'purchases': ([('move_id.move_type', 'in', ('in_invoice', 'in_refund')),
                   ('display_type', '=', 'product')], 1),
    'revenue': ([('account_id.account_type', 'in', ('income', 'income_other'))], -1),
    'expenses': ([('account_id.account_type', 'in', ('expense', 'expense_depreciation',
                                                     'expense_direct_cost'))], 1),
    'profit': ([('account_id.account_type', 'in', ('income', 'income_other', 'expense',
                                                   'expense_depreciation', 'expense_direct_cost'))], -1),
}

# Shared JSON-schema fragments. Short descriptions on purpose: tool schemas
# are re-sent with every request, so every word costs tokens.
# The period keywords are listed once in the system prompt rather than as an
# enum repeated in every tool schema (saves ~1,000 tokens per AI call).
P_PERIOD = {'type': 'string', 'description': 'Period keyword (see system prompt).'}
P_FROM = {'type': 'string', 'description': 'YYYY-MM-DD, with period=custom.'}
P_TO = {'type': 'string', 'description': 'YYYY-MM-DD, with period=custom.'}
P_CHART = {'type': 'string', 'enum': ['none', 'bar', 'line', 'pie'],
           'description': 'Chart shown to the user. Default none.'}
P_LIMIT = {'type': 'integer', 'description': 'Rows, default 10, max 50.'}
P_COMPARE = {'type': 'string', 'enum': ['none', 'previous_period', 'previous_year'],
             'description': 'Comparison column.'}
PERIOD_PARAMS = {'period': P_PERIOD, 'date_from': P_FROM, 'date_to': P_TO}
# (period, start, end) parameter triples resolved before a tool runs, and
# single date parameters.
PERIOD_KEYS = (('period', 'date_from', 'date_to'), ('period_a', 'a_from', 'a_to'),
               ('period_b', 'b_from', 'b_to'))
DATE_KEYS = ('as_of',)
# Tools whose input is free-form (domains, field names): database and ORM
# errors are an expected answer to a wrong call, not a bug.
GENERIC_TOOLS = ('query_records', 'describe_data')
P_PARTNER = {'type': 'string', 'description': 'Partner name.'}
P_DIMENSION = {'type': 'string', 'enum': [*BREAKDOWN_DIMENSIONS, 'analytic_account', *TIME_DIMENSIONS]}


class AiAccountingToolkit(models.AbstractModel):
    """Read-only tools the AI can call.

    Every tool returns a dict:

    * ``model``: compact data sent back to the AI (rounded, row-limited),
    * ``blocks``: what the user sees (tables, charts, KPI cards), rendered by
      the client from data and never re-typed by the AI,
    * ``digest``: a one-line summary kept in the conversation history.

    Tools run with the current user's access rights. To add a tool in another
    module, extend ``_ai_tool_specs`` and implement ``_ai_tool_<name>``.
    """
    _name = 'ai.accounting.toolkit'
    _description = 'AI Accounting Tools'

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------
    @api.model
    def _ai_tool_specs(self):
        return {
            'get_kpi_overview': {
                'description': 'Key figures: revenue, expenses, net profit, receivables, '
                               'payables, overdue, cash; with change vs previous period.',
                'parameters': {**PERIOD_PARAMS},
                'label': self.env._("Key figures"),
            },
            'get_profit_and_loss': {
                'description': 'Profit and loss statement for a period.',
                'parameters': {**PERIOD_PARAMS, 'compare': P_COMPARE,
                               'detail': {'type': 'string', 'enum': ['summary', 'accounts'],
                                          'description': 'Default summary.'},
                               'chart': P_CHART},
                'label': self.env._("Profit and Loss"),
            },
            'get_balance_sheet': {
                'description': 'Balance sheet at the end of the period (default today).',
                'parameters': {**PERIOD_PARAMS,
                               'detail': {'type': 'string', 'enum': ['summary', 'accounts']},
                               'chart': P_CHART},
                'label': self.env._("Balance Sheet"),
            },
            'get_trial_balance': {
                'description': 'Trial balance: accounts with debit, credit, balance.',
                'parameters': {**PERIOD_PARAMS, 'limit': P_LIMIT},
                'label': self.env._("Trial Balance"),
            },
            'get_aged_balance': {
                'description': 'Aged receivable or payable by partner, in 30-day buckets.',
                'parameters': {'kind': {'type': 'string', 'enum': ['receivable', 'payable']},
                               'as_of': {'type': 'string', 'description': 'YYYY-MM-DD, default today.'},
                               'limit': P_LIMIT, 'chart': P_CHART},
                'required': ['kind'],
                'label': self.env._("Aged Balance"),
            },
            'get_top_partners': {
                'description': 'Top customers (sales) or vendors (purchases) by untaxed amount.',
                'parameters': {'kind': {'type': 'string', 'enum': ['customer', 'vendor']},
                               **PERIOD_PARAMS, 'limit': P_LIMIT, 'chart': P_CHART},
                'required': ['kind'],
                'label': self.env._("Top partners"),
            },
            'get_top_products': {
                'description': 'Top products sold or purchased by amount or quantity.',
                'parameters': {'kind': {'type': 'string', 'enum': ['sale', 'purchase']},
                               **PERIOD_PARAMS,
                               'metric': {'type': 'string', 'enum': ['amount', 'quantity']},
                               'limit': P_LIMIT, 'chart': P_CHART},
                'required': ['kind'],
                'label': self.env._("Top products"),
            },
            'get_trend': {
                'description': 'Time series of revenue, expenses, profit, sales or purchases.',
                'parameters': {'metric': {'type': 'string', 'enum': [
                    'revenue', 'expenses', 'profit', 'sales', 'purchases']},
                    **PERIOD_PARAMS,
                    'granularity': {'type': 'string', 'enum': ['day', 'week', 'month', 'quarter', 'year']},
                    'chart': P_CHART},
                'required': ['metric'],
                'label': self.env._("Trend"),
            },
            'get_cash_balances': {
                'description': 'Bank and cash account balances at the end of the period.',
                'parameters': {**PERIOD_PARAMS, 'chart': P_CHART},
                'label': self.env._("Cash and bank"),
            },
            'get_invoices': {
                'description': 'List customer invoices or vendor bills with filters.',
                'parameters': {'kind': {'type': 'string', 'enum': ['customer', 'vendor']},
                               'status': {'type': 'string', 'enum': [
                                   'open', 'overdue', 'paid', 'draft', 'all']},
                               **PERIOD_PARAMS,
                               'partner': {'type': 'string', 'description': 'Partner name.'},
                               'order': {'type': 'string', 'enum': [
                                   'amount_desc', 'date_desc', 'due_asc']},
                               'limit': P_LIMIT},
                'required': ['kind'],
                'label': self.env._("Invoices"),
            },
            'get_tax_summary': {
                'description': 'Tax report: base and tax amount per tax, sales and purchases.',
                'parameters': {**PERIOD_PARAMS},
                'label': self.env._("Tax report"),
            },
            'get_partner_summary': {
                'description': 'One partner: balance due, overdue, sales and purchases in period.',
                'parameters': {'partner': {'type': 'string', 'description': 'Partner name.'},
                               **PERIOD_PARAMS},
                'required': ['partner'],
                'label': self.env._("Partner summary"),
            },
            'get_breakdown': {
                'description': 'Sales, purchases, revenue, expenses or profit grouped by a dimension, '
                               'optionally split by a second one (e.g. by month).',
                'parameters': {'measure': {'type': 'string', 'enum': list(BREAKDOWN_MEASURES)},
                               'group_by': P_DIMENSION, 'then_by': P_DIMENSION,
                               **PERIOD_PARAMS, 'partner': P_PARTNER,
                               'limit': P_LIMIT, 'chart': P_CHART},
                'required': ['measure', 'group_by'],
                'label': self.env._("Breakdown"),
            },
            'compare_periods': {
                'description': 'Revenue, expenses, profit, sales and purchases of two periods side by side.',
                'parameters': {'period_a': P_PERIOD, 'a_from': P_FROM, 'a_to': P_TO,
                               'period_b': P_PERIOD, 'b_from': P_FROM, 'b_to': P_TO,
                               'chart': P_CHART},
                'required': ['period_a', 'period_b'],
                'label': self.env._("Period comparison"),
            },
            'get_margins': {
                'description': 'Gross margin per product, customer or product category '
                               '(cost estimated from current product cost).',
                'parameters': {'group_by': {'type': 'string', 'enum': [
                    'product', 'customer', 'product_category']},
                    **PERIOD_PARAMS, 'limit': P_LIMIT, 'chart': P_CHART},
                'label': self.env._("Margins"),
            },
            'get_cash_forecast': {
                'description': 'Projected cash balance from open receivables and payables by due date.',
                'parameters': {'granularity': {'type': 'string', 'enum': ['week', 'month']},
                               'periods': {'type': 'integer', 'description': 'Buckets, default 8.'},
                               'chart': P_CHART},
                'label': self.env._("Cash forecast"),
            },
            'get_ratios': {
                'description': 'DSO, DPO, current and quick ratio, gross and net margin.',
                'parameters': {**PERIOD_PARAMS},
                'label': self.env._("Financial ratios"),
            },
            'get_payments': {
                'description': 'List payments received or sent.',
                'parameters': {'kind': {'type': 'string', 'enum': ['received', 'sent', 'all']},
                               **PERIOD_PARAMS, 'partner': P_PARTNER,
                               'status': {'type': 'string', 'enum': ['done', 'draft', 'all']},
                               'limit': P_LIMIT},
                'label': self.env._("Payments"),
            },
            'search_journal_items': {
                'description': 'Search posted journal items by account, partner, journal, text or amount.',
                'parameters': {**PERIOD_PARAMS,
                               'account': {'type': 'string', 'description': 'Account code or name.'},
                               'partner': P_PARTNER,
                               'journal': {'type': 'string', 'description': 'Journal name or code.'},
                               'text': {'type': 'string', 'description': 'In label or reference.'},
                               'min_amount': {'type': 'number'}, 'max_amount': {'type': 'number'},
                               'limit': P_LIMIT},
                'label': self.env._("Journal items"),
            },
            'get_invoice_details': {
                'description': 'One invoice or bill with its lines, by number.',
                'parameters': {'number': {'type': 'string'}},
                'required': ['number'],
                'label': self.env._("Invoice details"),
            },
            'query_records': {
                'description': 'Generic read-only query on any business model when no other tool fits '
                               '(e.g. count customers, list products). Returns records or grouped totals.',
                'parameters': {
                    'model': {'type': 'string', 'description': 'Technical model, e.g. res.partner.'},
                    'domain': {'type': 'string',
                               'description': 'Odoo domain as JSON, e.g. [["customer_rank",">",0]].'},
                    'fields': {'type': 'array', 'items': {'type': 'string'},
                               'description': 'Fields to show (max 8).'},
                    'group_by': {'type': 'array', 'items': {'type': 'string'},
                                 'description': 'Up to 2, dates as field:month.'},
                    'aggregate': {'type': 'string',
                                  'description': 'count (default) or field:sum|avg|min|max|count_distinct.'},
                    'order': {'type': 'string', 'description': 'e.g. "create_date desc".'},
                    'related': {
                        'type': 'object',
                        'description': 'Keep records that are (with) or are not (without) referenced by '
                                       'another model through a many2one, e.g. products never invoiced: '
                                       '{"mode":"without","model":"account.move.line","field":"product_id",'
                                       '"domain":"[[\\"move_id.move_type\\",\\"=\\",\\"out_invoice\\"]]"}.',
                        'properties': {
                            'mode': {'type': 'string', 'enum': ['with', 'without']},
                            'model': {'type': 'string'},
                            'field': {'type': 'string', 'description': 'many2one on that model.'},
                            'domain': {'type': 'string'},
                        },
                    },
                    'display': {'type': 'boolean',
                                'description': 'false for helper lookups that are not the answer.'},
                    'date_field': {'type': 'string',
                                   'description': 'Date/datetime field filtered by period, e.g. create_date.'},
                    **PERIOD_PARAMS,
                    'limit': P_LIMIT, 'chart': P_CHART},
                'required': ['model'],
                'label': self.env._("Data query"),
            },
            'describe_data': {
                'description': 'Find models by keyword, or list the fields of a model.',
                'parameters': {'model': {'type': 'string'},
                               'search': {'type': 'string', 'description': 'Keyword for models or fields.'}},
                'label': self.env._("Data dictionary"),
            },
            'get_unreconciled_bank_lines': {
                'description': 'Bank statement lines not reconciled yet.',
                'parameters': {'journal': {'type': 'string', 'description': 'Bank journal name.'},
                               'limit': P_LIMIT},
                'label': self.env._("Unreconciled bank lines"),
            },
        }

    @api.model
    def _ai_get_tool_definitions(self):
        """Tool definitions in the provider-neutral format, sorted by name so
        the request prefix stays byte-stable for prompt caching."""
        definitions = []
        for name, spec in sorted(self._ai_tool_specs().items()):
            schema = {'type': 'object', 'properties': spec['parameters']}
            if spec.get('required'):
                schema['required'] = spec['required']
            definitions.append({'name': name, 'description': spec['description'],
                                'parameters': schema})
        return definitions

    @api.model
    def _ai_resolve_tool_name(self, name):
        """Declared tool name for ``name``; models sometimes prefix it
        (``default_api.get_kpi_overview``) or change its case."""
        specs = self._ai_tool_specs()
        name = str(name or '').strip()
        if name in specs:
            return name
        candidate = normalize_key(re.split(r'[.:/]', name)[-1])
        return candidate if candidate in specs else None

    @api.model
    def _ai_run_tool(self, name, arguments):
        """Run a tool; never raises. Errors are returned to the AI so it can
        correct its call; unexpected ones are logged and flagged ``internal``."""
        specs = self._ai_tool_specs()
        started = time.monotonic()
        tool = self._ai_resolve_tool_name(name)
        scope, excluded = self._ai_company_scope()
        # Every tool, generic queries included (through the record rules),
        # covers the same companies.
        toolkit = self.with_context(allowed_company_ids=[self.env.company.id] + (scope - self.env.company).ids)
        if not tool:
            output = self._ai_error(self.env._("Unknown tool %(name)s. Tools: %(tools)s.",
                                               name=name, tools=', '.join(sorted(specs))))
        else:
            try:
                # A failing query must not abort the whole conversation.
                with self.env.cr.savepoint():
                    output = getattr(toolkit, '_ai_tool_%s' % tool)(toolkit._ai_normalize_arguments(tool, arguments))
            except (UserError, ValidationError, AccessError, ArgumentError) as error:
                output = self._ai_error(str(error))
            except Exception as error:  # noqa: BLE001 - a tool bug must not end the conversation
                if tool in GENERIC_TOOLS and isinstance(error, (ValueError, TypeError, KeyError, PsycopgError)):
                    # Values the ORM or the database refused in a free-form query.
                    output = self._ai_error(str(error).strip().split('\n')[0][:300])
                else:
                    _logger.exception("AI Analytics tool %s failed with arguments %s", tool, arguments)
                    output = self._ai_error(self.env._(
                        "The tool failed unexpectedly (%s). Answer with the other data you have.",
                        type(error).__name__))
                    output['internal'] = True
        if output.get('error') and tool in GENERIC_TOOLS:
            output['model']['hint'] = QUERY_HINT
        if not output.get('error') and isinstance(output.get('model'), dict):
            if len(scope) > 1:
                output['model']['companies'] = scope.mapped('name')
            if excluded:
                output['model']['excluded_companies'] = '%s (other currency)' % ', '.join(excluded.mapped('name'))
        output.setdefault('blocks', [])
        output['digest'] = str(output.get('digest') or '')[:MAX_DIGEST_LENGTH]
        output['label'] = str(output.get('label') or (specs[tool]['label'] if tool else name))[:MAX_LABEL_LENGTH]
        output['ms'] = int((time.monotonic() - started) * 1000)
        return output

    @api.model
    def _ai_company_scope(self):
        """``(scope, excluded)``: the figures cover the companies selected in
        the company switcher (branches included when selected, which the
        switcher does by default for a parent company), limited to those
        sharing the current company's currency, as amounts in different
        currencies cannot be added up; ``excluded`` lists the others."""
        currency = self.env.company.currency_id
        scope = self.env.companies.filtered(lambda company: company.currency_id == currency)
        return scope, self.env.companies - scope

    @api.model
    def _ai_normalize_arguments(self, name, arguments):
        """Arguments of tool ``name`` matching its schema exactly (see
        ``llm.arguments``), with periods resolved to a documented keyword or
        to custom dates; raises ArgumentError for calls that make no sense."""
        spec = self._ai_tool_specs()[name]
        schema = {'properties': spec['parameters'], 'required': spec.get('required') or []}
        arguments = normalize_arguments(schema, arguments)
        for keys in PERIOD_KEYS:
            if keys[0] in spec['parameters']:
                self._ai_normalize_period(arguments, *keys)
        for key in DATE_KEYS:
            if arguments.get(key):
                # "as of October" is the end of October.
                arguments[key] = fields.Date.to_string(self._ai_parse_date(arguments[key], end=True))
        check_required(schema, arguments)
        return arguments

    @api.model
    def _ai_normalize_period(self, arguments, period_key, from_key, to_key):
        """Resolve a period written in words (``october``, ``Q3 2026``, ``last
        7 days``) to custom dates; dates sent without ``period=custom`` mean a
        custom period (they are never silently ignored)."""
        today = fields.Date.context_today(self)
        date_from = self._ai_parse_date(arguments.get(from_key))
        date_to = self._ai_parse_date(arguments.get(to_key), end=True)
        period = arguments.get(period_key)
        if period:
            period, text_from, text_to = resolve_period_text(period, today, PERIODS)
            if text_to and not (date_from or date_to):
                date_from, date_to = text_from, text_to
        if (date_from or date_to) and (not period or period == 'custom' or (date_from and date_to)):
            period = 'custom'
        elif period != 'custom':
            date_from = date_to = False
        if period == 'custom' and not (date_from or date_to):
            raise ArgumentError("%s=custom needs %s and/or %s (YYYY-MM-DD)." % (period_key, from_key, to_key))
        if date_from and date_to and date_from > date_to:
            date_from, date_to = date_to, date_from
        for key, value in ((period_key, period), (from_key, date_from), (to_key, date_to)):
            if value:
                arguments[key] = fields.Date.to_string(value) if key != period_key else value
            else:
                arguments.pop(key, None)

    @api.model
    def _ai_error(self, message):
        message = str(message)
        if len(message) > MAX_ERROR_LENGTH:
            message = message[:MAX_ERROR_LENGTH - 1] + '…'
        return {'model': {'error': message}, 'error': True, 'digest': 'error: %s' % message}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @api.model
    def _ai_parse_date(self, value, end=False):
        """Date from an AI argument (see ``llm.arguments.parse_date``);
        ``01/10/2026`` is read with the day/month order of the user's
        language."""
        if not value:
            return False
        date_format = self.env['res.lang']._lang_get(self.env.lang or 'en_US').date_format or '%m/%d/%Y'
        dayfirst = date_format.find('%d') < date_format.find('%m')
        try:
            return parse_date(value, end=end, dayfirst=dayfirst)
        except ArgumentError as error:
            raise UserError(str(error)) from error

    @api.model
    def _ai_resolve_period(self, arguments, default='this_month'):
        """``(date_from, date_to)`` for the period arguments of a tool; date
        arithmetic is done here so the AI never spends tokens on it."""
        period = arguments.get('period') or default
        today = fields.Date.context_today(self)
        company = self.env.company
        if period == 'custom':
            date_from = self._ai_parse_date(arguments.get('date_from'))
            date_to = self._ai_parse_date(arguments.get('date_to')) or today
            if date_from and date_from > date_to:
                raise UserError(self.env._("The start date is after the end date."))
            return date_from, date_to
        if period == 'today':
            return today, today
        if period == 'yesterday':
            day = today - timedelta(days=1)
            return day, day
        if period in ('this_week', 'last_week'):
            start = today - timedelta(days=today.weekday())
            if period == 'last_week':
                start -= timedelta(days=7)
            return start, start + timedelta(days=6)
        if period in ('this_month', 'last_month'):
            day = today if period == 'this_month' else today - relativedelta(months=1)
            return date_utils.start_of(day, 'month'), date_utils.end_of(day, 'month')
        if period in ('this_quarter', 'last_quarter'):
            day = today if period == 'this_quarter' else today - relativedelta(months=3)
            return date_utils.start_of(day, 'quarter'), date_utils.end_of(day, 'quarter')
        if period in ('this_year', 'last_year', 'year_to_date'):
            fiscal = company.compute_fiscalyear_dates(today)
            if period == 'last_year':
                fiscal = company.compute_fiscalyear_dates(fiscal['date_from'] - timedelta(days=1))
            date_to = today if period == 'year_to_date' else fiscal['date_to']
            return fiscal['date_from'], date_to
        if period in ('last_30_days', 'last_90_days'):
            days = 30 if period == 'last_30_days' else 90
            return today - timedelta(days=days - 1), today
        if period == 'last_12_months':
            return date_utils.start_of(today - relativedelta(months=11), 'month'), \
                date_utils.end_of(today, 'month')
        if period == 'all_time':
            return False, today
        raise UserError(self.env._("Unknown period %(period)s. Use one of: %(periods)s.",
                                   period=period, periods=', '.join(PERIODS)))

    @api.model
    def _ai_previous_period(self, date_from, date_to, compare):
        if not date_from or compare == 'none':
            return False, False
        if compare == 'previous_year':
            return date_from - relativedelta(years=1), date_to - relativedelta(years=1)
        if date_from.day == 1 and date_to == date_utils.end_of(date_to, 'month'):
            months = (date_to.year - date_from.year) * 12 + date_to.month - date_from.month + 1
            prev_from = date_from - relativedelta(months=months)
            return prev_from, date_utils.end_of(date_from - relativedelta(days=1), 'month')
        length = date_to - date_from
        prev_to = date_from - timedelta(days=1)
        return prev_to - length, prev_to

    @api.model
    def _ai_period_label(self, date_from, date_to):
        if not date_from:
            return self.env._("up to %s", format_date(self.env, date_to))
        return '%s – %s' % (format_date(self.env, date_from), format_date(self.env, date_to))

    @api.model
    def _ai_iso(self, date_from, date_to):
        return '%s..%s' % (date_from or '', date_to)

    @api.model
    def _ai_limit(self, arguments, default=10):
        try:
            limit = int(arguments.get('limit') or default)
        except (TypeError, ValueError):
            limit = default
        return max(1, min(limit, MAX_ROWS))

    @api.model
    def _ai_model_rows(self):
        """Rows of a table sent back to the AI (the user sees all of them)."""
        return self.env['ir.config_parameter'].sudo().get_int(
            'ai_accounting_analytics.model_rows', 15) or 15

    @api.model
    def _ai_round(self, value):
        return round(value or 0.0, 2)

    @api.model
    def _ai_aml_domain(self, date_from=False, date_to=False, account_types=None):
        domain = [('parent_state', '=', 'posted'), ('company_id', 'in', self.env.companies.ids)]
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        if account_types:
            domain.append(('account_id.account_type', 'in', list(account_types)))
        return domain

    @api.model
    def _ai_sum(self, model, domain, field):
        result = self.env[model]._read_group(domain, [], ['%s:sum' % field])
        return result[0][0] or 0.0 if result else 0.0

    @api.model
    def _ai_table(self, title, columns, rows, export=None):
        """Display table. ``columns``: ``[(label, type)]`` with type in text,
        monetary, number, percent, date. ``rows``: ``[{'cells', 'level', 'bold'}]``."""
        block = {
            'type': 'table',
            'title': title,
            'columns': [{'label': label, 'type': kind} for label, kind in columns],
            'rows': rows,
            'currency_id': self.env.company.currency_id.id,
        }
        if export:
            block['export'] = export
        return block

    @api.model
    def _ai_chart(self, chart_type, title, labels, datasets):
        if not chart_type or chart_type == 'none' or not labels:
            return None
        if chart_type == 'pie':
            datasets = datasets[:1]
        return {
            'type': 'chart',
            'chart_type': chart_type,
            'title': title,
            'labels': [str(label) for label in labels],
            'datasets': [{'label': label, 'data': [self._ai_round(v) for v in data]}
                         for label, data in datasets],
            'currency_id': self.env.company.currency_id.id,
        }

    @api.model
    def _ai_compact_rows(self, rows):
        limit = self._ai_model_rows()
        compact = {'rows': rows[:limit]}
        if len(rows) > limit:
            compact['more_rows'] = len(rows) - limit
        return compact

    @api.model
    def _ai_digest(self, name, rows, size=5):
        preview = '; '.join(', '.join(str(cell) for cell in row) for row in rows[:size])
        return ('%s: %s' % (name, preview))[:400]

    @api.model
    def _ai_delta(self, current, previous):
        if not previous:
            return None
        return round((current - previous) / abs(previous) * 100, 1)

    @api.model
    def _ai_find_partner(self, name):
        Partner = self.env['res.partner']
        partners = Partner.search([('name', '=ilike', name)], limit=1) \
            or Partner.search([('name', 'ilike', name)], limit=6)
        if not partners:
            raise UserError(self.env._("No partner matches '%s'.", name))
        return partners

    # ------------------------------------------------------------------
    # Accounting Kit financial reports
    # ------------------------------------------------------------------
    @api.model
    def _ai_financial_lines(self, report_xmlid, date_from, date_to):
        report = self.env.ref(report_xmlid)
        data = {
            'account_report_id': [report.id, report.name],
            'enable_filter': False,
            'debit_credit': False,
            'used_context': {
                'date_from': date_from or False,
                'date_to': date_to,
                'strict_range': bool(date_from),
                'state': 'posted',
            },
        }
        return report, self.env['financial.report'].get_account_lines(data)

    @api.model
    def _ai_financial_statement(self, arguments, report_xmlid, title, balance_sheet=False):
        date_from, date_to = self._ai_resolve_period(arguments)
        if balance_sheet:
            date_from = False
        compare = arguments.get('compare') or 'none'
        detail = arguments.get('detail') or 'summary'
        report, lines = self._ai_financial_lines(report_xmlid, date_from, date_to)
        prev_from, prev_to = (False, False)
        previous = {}
        if not balance_sheet and compare != 'none':
            prev_from, prev_to = self._ai_previous_period(date_from, date_to, compare)
            if prev_to:
                _report, prev_lines = self._ai_financial_lines(report_xmlid, prev_from, prev_to)
                previous = {(line['type'], line.get('r_id') or line.get('account')):
                            line['balance'] for line in prev_lines}
        if detail == 'summary':
            lines = [line for line in lines if line['type'] == 'report']

        columns = [(self.env._("Line"), 'text'), (self.env._("Amount"), 'monetary')]
        if previous:
            columns += [(self.env._("Previous"), 'monetary'), (self.env._("Change %"), 'percent')]
        # Depth in the report tree (the kit's own ``level`` key mixes the
        # style override, a string, with the computed depth).
        depth = {report.id: report.level for report in self.env['account.financial.report'].browse(
            [line['r_id'] for line in lines if line['type'] == 'report'])}
        rows, model_rows, chart_labels, chart_values = [], [], [], []
        for line in lines:
            balance = self._ai_round(line['balance'])
            is_report = line['type'] == 'report'
            level = depth.get(line.get('r_id'), 0) if is_report else 3
            cells = [line['name'], balance]
            model_row = [line['name'], balance]
            if previous:
                prev = self._ai_round(previous.get((line['type'], line.get('r_id') or line.get('account')), 0.0))
                delta = self._ai_delta(balance, prev)
                cells += [prev, delta]
                model_row += [prev, delta]
            rows.append({'cells': cells, 'level': level, 'bold': is_report and level <= 1})
            model_rows.append(model_row)
            if is_report and level == 1:
                chart_labels.append(line['name'])
                chart_values.append(balance)
        period_label = self._ai_period_label(date_from, date_to)
        export = {
            'model': 'financial.report',
            'vals': {'account_report_id': report.id, 'date_from': date_from or False,
                     'date_to': date_to, 'target_move': 'posted', 'debit_credit': False,
                     'enable_filter': False},
            'pdf': 'view_report_pdf',
            'xlsx': 'action_print_xlsx',
        }
        blocks = [self._ai_table('%s · %s' % (title, period_label), columns, rows, export)]
        chart = self._ai_chart(arguments.get('chart'), title, chart_labels,
                               [(title, chart_values)])
        if chart:
            blocks.append(chart)
        model = {
            'report': title,
            'period': self._ai_iso(date_from, date_to),
            'currency': self.env.company.currency_id.name,
            'cols': ['line', 'amount'] + (['previous', 'change_pct'] if previous else []),
            **self._ai_compact_rows(model_rows),
        }
        if previous:
            model['previous_period'] = self._ai_iso(prev_from, prev_to)
        return {'model': model, 'blocks': blocks,
                'label': '%s · %s' % (title, period_label),
                'digest': self._ai_digest('%s %s' % (title, model['period']), model_rows)}

    def _ai_tool_get_profit_and_loss(self, arguments):
        return self._ai_financial_statement(
            arguments, 'base_accounting_kit.account_financial_report_profitandloss0',
            self.env._("Profit and Loss"))

    def _ai_tool_get_balance_sheet(self, arguments):
        if not arguments.get('period'):
            arguments['period'] = 'today'
        return self._ai_financial_statement(
            arguments, 'base_accounting_kit.account_financial_report_balancesheet0',
            self.env._("Balance Sheet"), balance_sheet=True)

    def _ai_tool_get_trial_balance(self, arguments):
        date_from, date_to = self._ai_resolve_period(arguments)
        context = {'date_from': date_from or False, 'date_to': date_to,
                   'strict_range': bool(date_from), 'state': 'posted'}
        accounts = self.env['account.account'].search([])
        lines = self.env['report.base_accounting_kit.report_trial_balance'].with_context(
            **context)._get_accounts(accounts, 'not_zero')
        lines = sorted(lines, key=lambda line: abs(line['balance']), reverse=True)
        limit = self._ai_limit(arguments, default=MAX_ROWS)
        rows, model_rows = [], []
        for line in lines[:limit]:
            name = '%s %s' % (line['code'] or '', line['name'])
            values = [self._ai_round(line['debit']), self._ai_round(line['credit']),
                      self._ai_round(line['balance'])]
            rows.append({'cells': [name, *values]})
            model_rows.append([name, *values])
        totals = [self._ai_round(sum(line[key] for line in lines))
                  for key in ('debit', 'credit', 'balance')]
        rows.append({'cells': [self.env._("Total"), *totals], 'bold': True})
        period_label = self._ai_period_label(date_from, date_to)
        export = {
            'model': 'account.balance.report',
            'vals': {'date_from': date_from or False, 'date_to': date_to,
                     'target_move': 'posted', 'display_account': 'not_zero'},
            'pdf': 'check_report',
            'xlsx': 'action_print_xlsx',
        }
        table = self._ai_table(
            '%s · %s' % (self.env._("Trial Balance"), period_label),
            [(self.env._("Account"), 'text'), (self.env._("Debit"), 'monetary'),
             (self.env._("Credit"), 'monetary'), (self.env._("Balance"), 'monetary')],
            rows, export)
        model = {'period': self._ai_iso(date_from, date_to),
                 'cols': ['account', 'debit', 'credit', 'balance'],
                 'totals': totals, 'accounts': len(lines), **self._ai_compact_rows(model_rows)}
        return {'model': model, 'blocks': [table], 'label': table['title'],
                'digest': self._ai_digest('trial balance %s' % model['period'], model_rows)}

    def _ai_tool_get_aged_balance(self, arguments):
        kind = arguments.get('kind') or 'receivable'
        as_of = self._ai_parse_date(arguments.get('as_of')) or fields.Date.context_today(self)
        account_type = ['asset_receivable'] if kind == 'receivable' else ['liability_payable']
        partner_lines, totals, _lines = self.env[
            'report.base_accounting_kit.report_agedpartnerbalance'].with_context(
            company_ids=self.env.companies.ids)._get_partner_move_lines(
            account_type, fields.Date.to_string(as_of), 'posted', 30)
        sign = 1 if kind == 'receivable' else -1
        buckets = [('direction', self.env._("Not due")), ('4', '1-30'), ('3', '31-60'),
                   ('2', '61-90'), ('1', '91-120'), ('0', '+120')]
        partner_lines = sorted(partner_lines, key=lambda line: abs(line['total']), reverse=True)
        limit = self._ai_limit(arguments)
        rows, model_rows = [], []
        for line in partner_lines[:limit]:
            values = [self._ai_round(sign * line[key]) for key, _label in buckets]
            total = self._ai_round(sign * line['total'])
            rows.append({'cells': [line['name'], *values, total]})
            model_rows.append([line['name'], *values, total])
        # ``totals``: indexes 0-4 are the periods (0 = 1-30 ... 4 = +120),
        # 5 the grand total and 6 the not-due amount.
        total_values = [self._ai_round(sign * value) for value in
                        (totals[6], totals[4], totals[3], totals[2], totals[1], totals[0])] \
            if totals else [0.0] * 6
        grand_total = self._ai_round(sum(total_values))
        rows.append({'cells': [self.env._("Total"), *total_values, grand_total], 'bold': True})
        title = self.env._("Aged Receivable") if kind == 'receivable' else self.env._("Aged Payable")
        export = {
            'model': 'account.aged.trial.balance',
            'vals': {'date_from': as_of, 'period_length': 30, 'target_move': 'posted',
                     'result_selection': 'customer' if kind == 'receivable' else 'supplier'},
            'pdf': 'check_report',
            'xlsx': 'action_print_xlsx',
        }
        columns = [(self.env._("Partner"), 'text')] + [(label, 'monetary') for _key, label in buckets] \
            + [(self.env._("Total"), 'monetary')]
        blocks = [self._ai_table('%s · %s' % (title, format_date(self.env, as_of)),
                                 columns, rows, export)]
        chart = self._ai_chart(arguments.get('chart'), title,
                               [label for _key, label in buckets], [(title, total_values)])
        if chart:
            blocks.append(chart)
        model = {'as_of': str(as_of), 'cols': ['partner', 'not_due', '1-30', '31-60', '61-90',
                                               '91-120', '+120', 'total'],
                 'totals': total_values + [grand_total], 'partners': len(partner_lines),
                 **self._ai_compact_rows(model_rows)}
        return {'model': model, 'blocks': blocks, 'label': blocks[0]['title'],
                'digest': self._ai_digest('%s %s' % (title, as_of), model_rows)}

    # ------------------------------------------------------------------
    # ORM based analytics
    # ------------------------------------------------------------------
    @api.model
    def _ai_profit_figures(self, date_from, date_to):
        domain = self._ai_aml_domain(date_from, date_to)
        revenue = -self._ai_sum('account.move.line', domain + [
            ('account_id.account_type', 'in', INCOME_TYPES)], 'balance')
        expenses = self._ai_sum('account.move.line', domain + [
            ('account_id.account_type', 'in', EXPENSE_TYPES)], 'balance')
        return revenue, expenses

    def _ai_tool_get_kpi_overview(self, arguments):
        date_from, date_to = self._ai_resolve_period(arguments)
        today = fields.Date.context_today(self)
        revenue, expenses = self._ai_profit_figures(date_from, date_to)
        prev_from, prev_to = self._ai_previous_period(date_from, date_to, 'previous_period')
        prev_revenue, prev_expenses = self._ai_profit_figures(prev_from, prev_to) \
            if prev_to else (0.0, 0.0)
        open_domain = [('parent_state', '=', 'posted'), ('company_id', 'in', self.env.companies.ids),
                       ('reconciled', '=', False)]
        receivable_domain = open_domain + [('account_id.account_type', '=', 'asset_receivable')]
        payable_domain = open_domain + [('account_id.account_type', '=', 'liability_payable')]
        receivable = self._ai_sum('account.move.line', receivable_domain, 'amount_residual')
        overdue = self._ai_sum('account.move.line', receivable_domain + [
            ('date_maturity', '<', today)], 'amount_residual')
        payable = -self._ai_sum('account.move.line', payable_domain, 'amount_residual')
        cash = self._ai_sum('account.move.line', self._ai_aml_domain(
            False, date_to, ('asset_cash',)), 'balance')
        profit, prev_profit = revenue - expenses, prev_revenue - prev_expenses
        items = [
            (self.env._("Revenue"), revenue, self._ai_delta(revenue, prev_revenue)),
            (self.env._("Expenses"), expenses, self._ai_delta(expenses, prev_expenses)),
            (self.env._("Net Profit"), profit, self._ai_delta(profit, prev_profit)),
            (self.env._("Receivables"), receivable, None),
            (self.env._("Overdue Receivables"), overdue, None),
            (self.env._("Payables"), payable, None),
            (self.env._("Cash and Bank"), cash, None),
        ]
        period_label = self._ai_period_label(date_from, date_to)
        block = {
            'type': 'kpis',
            'title': '%s · %s' % (self.env._("Key figures"), period_label),
            'items': [{'label': label, 'value': self._ai_round(value), 'delta': delta}
                      for label, value, delta in items],
            'currency_id': self.env.company.currency_id.id,
        }
        model = {
            'period': self._ai_iso(date_from, date_to),
            'previous_period': self._ai_iso(prev_from, prev_to) if prev_to else None,
            'currency': self.env.company.currency_id.name,
            'revenue': self._ai_round(revenue), 'revenue_prev': self._ai_round(prev_revenue),
            'expenses': self._ai_round(expenses), 'expenses_prev': self._ai_round(prev_expenses),
            'net_profit': self._ai_round(profit), 'net_profit_prev': self._ai_round(prev_profit),
            'receivables': self._ai_round(receivable), 'overdue_receivables': self._ai_round(overdue),
            'payables': self._ai_round(payable), 'cash': self._ai_round(cash),
        }
        return {'model': model, 'blocks': [block], 'label': block['title'],
                'digest': 'kpi %s: revenue %s, expenses %s, profit %s, cash %s' % (
                    model['period'], model['revenue'], model['expenses'],
                    model['net_profit'], model['cash'])}

    def _ai_tool_get_top_partners(self, arguments):
        kind = arguments.get('kind') or 'customer'
        date_from, date_to = self._ai_resolve_period(arguments, default='this_year')
        limit = self._ai_limit(arguments)
        sign = 1 if kind == 'customer' else -1
        domain = [('state', '=', 'posted'), ('company_id', 'in', self.env.companies.ids),
                  ('move_type', 'in', CUSTOMER_MOVE_TYPES if kind == 'customer' else VENDOR_MOVE_TYPES),
                  ('invoice_date', '<=', date_to)]
        if date_from:
            domain.append(('invoice_date', '>=', date_from))
        order = 'amount_untaxed_signed:sum %s' % ('desc' if kind == 'customer' else 'asc')
        groups = self.env['account.move']._read_group(
            domain, ['partner_id'], ['amount_untaxed_signed:sum', '__count'],
            order=order, limit=limit)
        total = sign * self._ai_sum('account.move', domain, 'amount_untaxed_signed')
        rows, model_rows = [], []
        for partner, amount, count in groups:
            amount = self._ai_round(sign * amount)
            share = round(amount / total * 100, 1) if total else None
            name = partner.display_name or self.env._("Unknown")
            rows.append({'cells': [name, count, amount, share]})
            model_rows.append([name, count, amount, share])
        title = self.env._("Top Customers") if kind == 'customer' else self.env._("Top Vendors")
        period_label = self._ai_period_label(date_from, date_to)
        blocks = [self._ai_table(
            '%s · %s' % (title, period_label),
            [(self.env._("Partner"), 'text'), (self.env._("Invoices"), 'number'),
             (self.env._("Untaxed Amount"), 'monetary'), (self.env._("Share %"), 'percent')],
            rows)]
        chart = self._ai_chart(arguments.get('chart'), title, [row[0] for row in model_rows],
                               [(self.env._("Untaxed Amount"), [row[2] for row in model_rows])])
        if chart:
            blocks.append(chart)
        model = {'period': self._ai_iso(date_from, date_to), 'total': self._ai_round(total),
                 'cols': ['partner', 'invoices', 'untaxed', 'share_pct'],
                 **self._ai_compact_rows(model_rows)}
        return {'model': model, 'blocks': blocks, 'label': blocks[0]['title'],
                'digest': self._ai_digest('%s %s' % (title, model['period']), model_rows)}

    def _ai_tool_get_top_products(self, arguments):
        kind = arguments.get('kind') or 'sale'
        metric = arguments.get('metric') or 'amount'
        date_from, date_to = self._ai_resolve_period(arguments, default='this_year')
        limit = self._ai_limit(arguments)
        move_types = CUSTOMER_MOVE_TYPES if kind == 'sale' else VENDOR_MOVE_TYPES
        domain = self._ai_aml_domain(date_from, date_to) + [
            ('move_id.move_type', 'in', move_types), ('display_type', '=', 'product'),
            ('product_id', '!=', False)]
        sign = -1 if kind == 'sale' else 1
        aggregate = 'balance:sum' if metric == 'amount' else 'quantity:sum'
        order = aggregate + (' asc' if kind == 'sale' and metric == 'amount' else ' desc')
        groups = self.env['account.move.line']._read_group(
            domain, ['product_id'], ['balance:sum', 'quantity:sum'], order=order, limit=limit)
        rows, model_rows = [], []
        for product, balance, quantity in groups:
            amount = self._ai_round(sign * balance)
            rows.append({'cells': [product.display_name, self._ai_round(quantity), amount]})
            model_rows.append([product.display_name, self._ai_round(quantity), amount])
        title = self.env._("Top Products Sold") if kind == 'sale' else self.env._("Top Products Purchased")
        period_label = self._ai_period_label(date_from, date_to)
        blocks = [self._ai_table(
            '%s · %s' % (title, period_label),
            [(self.env._("Product"), 'text'), (self.env._("Quantity"), 'number'),
             (self.env._("Amount"), 'monetary')], rows)]
        value_index = 2 if metric == 'amount' else 1
        chart = self._ai_chart(arguments.get('chart'), title, [row[0] for row in model_rows],
                               [(title, [row[value_index] for row in model_rows])])
        if chart:
            blocks.append(chart)
        model = {'period': self._ai_iso(date_from, date_to), 'cols': ['product', 'qty', 'amount'],
                 **self._ai_compact_rows(model_rows)}
        return {'model': model, 'blocks': blocks, 'label': blocks[0]['title'],
                'digest': self._ai_digest('%s %s' % (title, model['period']), model_rows)}

    def _ai_tool_get_trend(self, arguments):
        metric = arguments.get('metric') or 'revenue'
        granularity = arguments.get('granularity') or 'month'
        date_from, date_to = self._ai_resolve_period(arguments, default='last_12_months')
        if not date_from:
            date_from = date_utils.start_of(date_to - relativedelta(months=11), 'month')
        series = {}
        if metric in ('sales', 'purchases'):
            move_types = CUSTOMER_MOVE_TYPES if metric == 'sales' else VENDOR_MOVE_TYPES
            sign = 1 if metric == 'sales' else -1
            series = self._ai_daily_series(
                'account.move', [('state', '=', 'posted'), ('company_id', 'in', self.env.companies.ids),
                                 ('move_type', 'in', move_types), ('invoice_date', '>=', date_from),
                                 ('invoice_date', '<=', date_to)],
                'invoice_date', 'amount_untaxed_signed:sum', granularity)
            series = {key: sign * value for key, value in series.items()}
        else:
            domain = self._ai_aml_domain(date_from, date_to)
            revenue = {key: -value for key, value in self._ai_daily_series(
                'account.move.line', domain + [('account_id.account_type', 'in', INCOME_TYPES)],
                'date', 'balance:sum', granularity).items()}
            expenses = self._ai_daily_series(
                'account.move.line', domain + [('account_id.account_type', 'in', EXPENSE_TYPES)],
                'date', 'balance:sum', granularity)
            if metric == 'revenue':
                series = revenue
            elif metric == 'expenses':
                series = expenses
            else:
                series = {key: revenue.get(key, 0.0) - expenses.get(key, 0.0)
                          for key in set(revenue) | set(expenses)}
        # Fill the gaps so the chart shows every bucket.
        step = {'day': relativedelta(days=1), 'week': relativedelta(weeks=1),
                'month': relativedelta(months=1), 'quarter': relativedelta(months=3),
                'year': relativedelta(years=1)}[granularity]
        bucket = self._ai_bucket_start(date_from, granularity)
        labels, values = [], []
        while bucket <= date_to and len(labels) < 400:
            labels.append(self._ai_bucket_label(bucket, granularity))
            values.append(self._ai_round(series.get(bucket, 0.0)))
            bucket += step
        title = {
            'revenue': self.env._("Revenue"), 'expenses': self.env._("Expenses"),
            'profit': self.env._("Net Profit"), 'sales': self.env._("Sales (untaxed)"),
            'purchases': self.env._("Purchases (untaxed)"),
        }[metric]
        period_label = self._ai_period_label(date_from, date_to)
        rows = [{'cells': [label, value]} for label, value in zip(labels, values)]
        rows.append({'cells': [self.env._("Total"), self._ai_round(sum(values))], 'bold': True})
        blocks = []
        chart = self._ai_chart(arguments.get('chart') or 'line', title, labels, [(title, values)])
        if chart:
            blocks.append(chart)
        blocks.append(self._ai_table('%s · %s' % (title, period_label),
                                     [(self.env._("Period"), 'text'), (title, 'monetary')], rows))
        model_rows = [[label, value] for label, value in zip(labels, values)]
        model = {'metric': metric, 'period': self._ai_iso(date_from, date_to),
                 'total': self._ai_round(sum(values)), 'cols': [granularity, 'amount'],
                 'rows': model_rows[-self._ai_model_rows():]}
        return {'model': model, 'blocks': blocks, 'label': '%s · %s' % (title, period_label),
                'digest': self._ai_digest('%s by %s' % (metric, granularity), model_rows[-6:], size=6)}

    @api.model
    def _ai_bucket_start(self, day, granularity):
        """Start of the period containing ``day`` (ISO weeks: Monday)."""
        if granularity == 'week':
            return day - timedelta(days=day.weekday())
        return date_utils.start_of(day, granularity)

    @api.model
    def _ai_daily_series(self, model, domain, date_field, aggregate, granularity):
        """``{bucket_start: total}`` grouped per day in SQL and rolled up here,
        so buckets do not depend on the user's locale week start."""
        series = defaultdict(float)
        for day, value in self.env[model]._read_group(domain, ['%s:day' % date_field], [aggregate]):
            if day:
                series[self._ai_bucket_start(day, granularity)] += value or 0.0
        return series

    @api.model
    def _ai_bucket_label(self, day, granularity):
        if granularity == 'month':
            return format_date(self.env, day, date_format='MMM yyyy')
        if granularity == 'quarter':
            return 'Q%s %s' % ((day.month - 1) // 3 + 1, day.year)
        if granularity == 'year':
            return str(day.year)
        return format_date(self.env, day)

    def _ai_tool_get_cash_balances(self, arguments):
        if not arguments.get('period'):
            arguments['period'] = 'today'
        _date_from, date_to = self._ai_resolve_period(arguments)
        groups = self.env['account.move.line']._read_group(
            self._ai_aml_domain(False, date_to, ('asset_cash',)),
            ['account_id'], ['balance:sum'], order='balance:sum desc')
        rows, model_rows = [], []
        for account, balance in groups:
            rows.append({'cells': [account.display_name, self._ai_round(balance)]})
            model_rows.append([account.display_name, self._ai_round(balance)])
        total = self._ai_round(sum(row[1] for row in model_rows))
        rows.append({'cells': [self.env._("Total"), total], 'bold': True})
        title = self.env._("Cash and Bank")
        blocks = [self._ai_table('%s · %s' % (title, format_date(self.env, date_to)),
                                 [(self.env._("Account"), 'text'), (self.env._("Balance"), 'monetary')],
                                 rows)]
        chart = self._ai_chart(arguments.get('chart'), title, [row[0] for row in model_rows],
                               [(title, [row[1] for row in model_rows])])
        if chart:
            blocks.append(chart)
        model = {'as_of': str(date_to), 'total': total, 'cols': ['account', 'balance'],
                 **self._ai_compact_rows(model_rows)}
        return {'model': model, 'blocks': blocks, 'label': blocks[0]['title'],
                'digest': self._ai_digest('cash %s total %s' % (date_to, total), model_rows)}

    def _ai_tool_get_invoices(self, arguments):
        kind = arguments.get('kind') or 'customer'
        status = arguments.get('status') or 'open'
        today = fields.Date.context_today(self)
        domain = [('company_id', 'in', self.env.companies.ids),
                  ('move_type', 'in', CUSTOMER_MOVE_TYPES if kind == 'customer' else VENDOR_MOVE_TYPES)]
        if arguments.get('period'):
            date_from, date_to = self._ai_resolve_period(arguments)
            domain.append(('invoice_date', '<=', date_to))
            if date_from:
                domain.append(('invoice_date', '>=', date_from))
        if status == 'draft':
            domain.append(('state', '=', 'draft'))
        else:
            domain.append(('state', '=', 'posted'))
            if status in ('open', 'overdue'):
                domain.append(('payment_state', 'in', ('not_paid', 'partial')))
            if status == 'overdue':
                domain.append(('invoice_date_due', '<', today))
            if status == 'paid':
                domain.append(('payment_state', 'in', ('paid', 'in_payment')))
        if arguments.get('partner'):
            partners = self._ai_find_partner(arguments['partner'])
            domain.append(('commercial_partner_id', 'in', partners.commercial_partner_id.ids))
        order = {'amount_desc': 'amount_total_signed desc' if kind == 'customer'
                 else 'amount_total_signed asc',
                 'date_desc': 'invoice_date desc, id desc',
                 'due_asc': 'invoice_date_due asc, id'}.get(arguments.get('order'), 'invoice_date desc, id desc')
        Move = self.env['account.move']
        limit = self._ai_limit(arguments)
        moves = Move.search(domain, order=order, limit=limit)
        count = Move.search_count(domain)
        sign = 1 if kind == 'customer' else -1
        residual_total = sign * self._ai_sum('account.move', domain, 'amount_residual_signed')
        total = sign * self._ai_sum('account.move', domain, 'amount_total_signed')
        rows, model_rows = [], []
        for move in moves:
            days_late = (today - move.invoice_date_due).days \
                if move.invoice_date_due and move.payment_state in ('not_paid', 'partial') \
                and move.invoice_date_due < today else 0
            values = [move.name, move.partner_id.display_name or '',
                      str(move.invoice_date or ''), str(move.invoice_date_due or ''),
                      self._ai_round(sign * move.amount_total_signed),
                      self._ai_round(sign * move.amount_residual_signed), days_late]
            rows.append({'cells': values, 'res_model': 'account.move', 'res_id': move.id})
            model_rows.append(values)
        title = self.env._("Customer Invoices") if kind == 'customer' else self.env._("Vendor Bills")
        table = self._ai_table(
            '%s · %s (%s)' % (title, dict(self._ai_status_labels())[status], count),
            [(self.env._("Number"), 'text'), (self.env._("Partner"), 'text'),
             (self.env._("Date"), 'date'), (self.env._("Due"), 'date'),
             (self.env._("Total"), 'monetary'), (self.env._("Amount Due"), 'monetary'),
             (self.env._("Days Late"), 'number')], rows)
        model = {'status': status, 'count': count, 'total': self._ai_round(total),
                 'amount_due': self._ai_round(residual_total),
                 'cols': ['number', 'partner', 'date', 'due', 'total', 'due_amount', 'days_late'],
                 **self._ai_compact_rows(model_rows)}
        return {'model': model, 'blocks': [table], 'label': table['title'],
                'digest': self._ai_digest('%s %s: %s, due %s' % (title, status, count,
                                                                   model['amount_due']), model_rows, size=3)}

    @api.model
    def _ai_status_labels(self):
        return [('open', self.env._("Open")), ('overdue', self.env._("Overdue")),
                ('paid', self.env._("Paid")), ('draft', self.env._("Draft")),
                ('all', self.env._("All"))]

    def _ai_tool_get_tax_summary(self, arguments):
        date_from, date_to = self._ai_resolve_period(arguments)
        groups = self.env['report.base_accounting_kit.report_tax'].with_context(
            state='posted').get_lines(
            {'date_from': date_from and fields.Date.to_string(date_from),
             'date_to': fields.Date.to_string(date_to)})
        rows, model_rows = [], []
        totals = {}
        for section, label in (('sale', self.env._("Sales")), ('purchase', self.env._("Purchases"))):
            taxes = groups.get(section) or []
            net = self._ai_round(sum(tax['net'] for tax in taxes))
            tax_amount = self._ai_round(sum(tax['tax'] for tax in taxes))
            totals[section] = tax_amount
            rows.append({'cells': [label, net, tax_amount], 'bold': True})
            for tax in taxes:
                rows.append({'cells': [tax['name'], self._ai_round(tax['net']),
                                       self._ai_round(tax['tax'])], 'level': 1})
                model_rows.append([section, tax['name'], self._ai_round(tax['net']),
                                   self._ai_round(tax['tax'])])
        balance = self._ai_round(totals.get('sale', 0.0) - totals.get('purchase', 0.0))
        rows.append({'cells': [self.env._("Net tax (sales - purchases)"), None, balance], 'bold': True})
        period_label = self._ai_period_label(date_from, date_to)
        export = {
            'model': 'kit.account.tax.report',
            'vals': {'date_from': date_from or False, 'date_to': date_to, 'target_move': 'posted'},
            'pdf': 'check_report',
            'xlsx': 'action_print_xlsx',
        }
        table = self._ai_table('%s · %s' % (self.env._("Tax Report"), period_label),
                               [(self.env._("Tax"), 'text'), (self.env._("Base"), 'monetary'),
                                (self.env._("Tax Amount"), 'monetary')], rows, export)
        model = {'period': self._ai_iso(date_from, date_to), 'sales_tax': totals.get('sale', 0.0),
                 'purchase_tax': totals.get('purchase', 0.0), 'net_tax': balance,
                 'cols': ['type', 'tax', 'base', 'tax_amount'], **self._ai_compact_rows(model_rows)}
        return {'model': model, 'blocks': [table], 'label': table['title'],
                'digest': 'tax %s: sales %s, purchases %s, net %s' % (
                    model['period'], model['sales_tax'], model['purchase_tax'], balance)}

    def _ai_tool_get_partner_summary(self, arguments):
        partners = self._ai_find_partner(arguments.get('partner') or '')
        if len(partners) > 1:
            names = partners.mapped('display_name')
            return {'model': {'ambiguous': True, 'candidates': names},
                    'digest': 'partner ambiguous: %s' % ', '.join(names)}
        partner = partners.commercial_partner_id
        date_from, date_to = self._ai_resolve_period(arguments, default='this_year')
        today = fields.Date.context_today(self)
        open_domain = [('parent_state', '=', 'posted'), ('company_id', 'in', self.env.companies.ids),
                       ('reconciled', '=', False), ('partner_id', 'child_of', partner.id)]
        receivable_domain = open_domain + [('account_id.account_type', '=', 'asset_receivable')]
        receivable = self._ai_sum('account.move.line', receivable_domain, 'amount_residual')
        overdue = self._ai_sum('account.move.line', receivable_domain + [
            ('date_maturity', '<', today)], 'amount_residual')
        payable = -self._ai_sum('account.move.line', open_domain + [
            ('account_id.account_type', '=', 'liability_payable')], 'amount_residual')
        invoice_domain = [('state', '=', 'posted'), ('company_id', 'in', self.env.companies.ids),
                          ('commercial_partner_id', '=', partner.id), ('invoice_date', '<=', date_to)]
        if date_from:
            invoice_domain.append(('invoice_date', '>=', date_from))
        sales = self._ai_sum('account.move', invoice_domain + [
            ('move_type', 'in', CUSTOMER_MOVE_TYPES)], 'amount_untaxed_signed')
        purchases = -self._ai_sum('account.move', invoice_domain + [
            ('move_type', 'in', VENDOR_MOVE_TYPES)], 'amount_untaxed_signed')
        period_label = self._ai_period_label(date_from, date_to)
        items = [
            (self.env._("Receivable"), receivable), (self.env._("Overdue"), overdue),
            (self.env._("Payable"), payable),
            (self.env._("Sales (untaxed) · %s", period_label), sales),
            (self.env._("Purchases (untaxed) · %s", period_label), purchases),
        ]
        block = {
            'type': 'kpis',
            'title': partner.display_name,
            'items': [{'label': label, 'value': self._ai_round(value), 'delta': None}
                      for label, value in items],
            'currency_id': self.env.company.currency_id.id,
            'res_model': 'res.partner',
            'res_id': partner.id,
        }
        model = {'partner': partner.display_name, 'period': self._ai_iso(date_from, date_to),
                 'receivable': self._ai_round(receivable), 'overdue': self._ai_round(overdue),
                 'payable': self._ai_round(payable), 'sales': self._ai_round(sales),
                 'purchases': self._ai_round(purchases),
                 'credit_limit_blocking': partner.blocking_stage or None}
        return {'model': model, 'blocks': [block], 'label': partner.display_name,
                'digest': 'partner %s: receivable %s, overdue %s, sales %s' % (
                    partner.display_name, model['receivable'], model['overdue'], model['sales'])}

    # ------------------------------------------------------------------
    # Breakdowns and analysis
    # ------------------------------------------------------------------
    @api.model
    def _ai_group_label(self, value, dimension):
        if dimension in TIME_DIMENSIONS:
            return self._ai_bucket_label(value, dimension) if value else self.env._("Undefined")
        return value.display_name if value else self.env._("Undefined")

    @api.model
    def _ai_sort_key(self, value, dimension):
        if dimension in TIME_DIMENSIONS:
            return value or fields.Date.to_date('1900-01-01')
        return value.id if value else 0

    def _ai_tool_get_breakdown(self, arguments):
        measure = arguments.get('measure') or 'sales'
        group_by = arguments.get('group_by') or 'partner'
        then_by = arguments.get('then_by') if arguments.get('then_by') != group_by else None
        if measure not in BREAKDOWN_MEASURES:
            raise UserError(self.env._("Unknown measure %s.", measure))
        for dimension in filter(None, (group_by, then_by)):
            if dimension not in BREAKDOWN_DIMENSIONS and dimension != 'analytic_account' \
                    and dimension not in TIME_DIMENSIONS:
                raise UserError(self.env._("Unknown dimension %s.", dimension))
        date_from, date_to = self._ai_resolve_period(arguments, default='this_year')
        limit = self._ai_limit(arguments)
        analytic = 'analytic_account' in (group_by, then_by)
        if analytic:
            # Analytic lines carry the amounts of the analytic distribution.
            Model = self.env['account.analytic.line']
            types = {'sales': INCOME_TYPES, 'revenue': INCOME_TYPES, 'purchases': EXPENSE_TYPES,
                     'expenses': EXPENSE_TYPES}.get(measure, INCOME_TYPES + EXPENSE_TYPES)
            domain = [('company_id', 'in', self.env.companies.ids),
                      ('general_account_id.account_type', 'in', list(types))]
            if date_from:
                domain.append(('date', '>=', date_from))
            domain.append(('date', '<=', date_to))
            sign = -1 if measure in ('purchases', 'expenses') else 1
            paths = {'partner': 'partner_id', 'account': 'general_account_id', 'product': 'product_id'}
            aggregate = 'amount:sum'
        else:
            Model = self.env['account.move.line']
            extra, sign = BREAKDOWN_MEASURES[measure]
            domain = self._ai_aml_domain(date_from, date_to) + extra
            paths = BREAKDOWN_DIMENSIONS
            aggregate = 'balance:sum'
        if arguments.get('partner'):
            partners = self._ai_find_partner(arguments['partner'])
            domain.append(('partner_id', 'child_of', partners.commercial_partner_id.ids))

        def groupby_spec(dimension):
            if dimension in TIME_DIMENSIONS:
                return 'date:%s' % dimension
            if dimension not in paths:
                raise UserError(self.env._("%(dimension)s cannot be combined with this breakdown.",
                                           dimension=dimension))
            return paths[dimension]

        if analytic:
            # Each root analytic plan has its own column on analytic lines.
            project_plan, other_plans = self.env['account.analytic.plan']._get_all_plans()
            groups = []
            for plan in project_plan + other_plans:
                paths['analytic_account'] = plan._column_name()
                groupby = [groupby_spec(group_by)] + ([groupby_spec(then_by)] if then_by else [])
                groups += [row for row in Model._read_group(domain, groupby, [aggregate])
                           if 'analytic_account' not in (group_by, then_by)
                           or row[(group_by, then_by).index('analytic_account')]]
        else:
            groupby = [groupby_spec(group_by)] + ([groupby_spec(then_by)] if then_by else [])
            groups = Model._read_group(domain, groupby, [aggregate])
        totals, cells, column_totals = defaultdict(float), defaultdict(float), defaultdict(float)
        for row in groups:
            key, column, value = row[0], (row[1] if then_by else None), sign * (row[-1] or 0.0)
            totals[key] += value
            cells[key, column] += value
            column_totals[column] += value
        if group_by in TIME_DIMENSIONS:
            keys = sorted(totals, key=lambda key: self._ai_sort_key(key, group_by))
            others = []
        else:
            keys = sorted(totals, key=lambda key: totals[key], reverse=True)
            keys, others = keys[:limit], keys[limit:]
        grand_total = self._ai_round(sum(totals.values()))
        columns_keys = []
        if then_by:
            columns_keys = sorted(column_totals, key=lambda key: self._ai_sort_key(key, then_by)) \
                if then_by in TIME_DIMENSIONS else \
                sorted(column_totals, key=lambda key: column_totals[key], reverse=True)[:8]

        rows, model_rows = [], []
        for key in keys:
            label = self._ai_group_label(key, group_by)
            if then_by:
                values = [self._ai_round(cells[key, column]) for column in columns_keys]
                cells_out = [label, *values, self._ai_round(totals[key])]
            else:
                share = round(totals[key] / grand_total * 100, 1) if grand_total else None
                cells_out = [label, self._ai_round(totals[key]), share]
            rows.append({'cells': cells_out})
            model_rows.append(cells_out)
        if others:
            other_total = self._ai_round(sum(totals[key] for key in others))
            rows.append({'cells': [self.env._("Others (%s)", len(others)), *(
                [None] * len(columns_keys) if then_by else []), other_total] + ([] if then_by else [None])})
        rows.append({'cells': [self.env._("Total"), *(
            [self._ai_round(column_totals[column]) for column in columns_keys] if then_by else []),
            grand_total] + ([] if then_by else [100.0 if grand_total else None]), 'bold': True})

        dimension_label = group_by.replace('_', ' ').title()
        measure_label = measure.title()
        if then_by:
            column_labels = [self._ai_group_label(column, then_by) for column in columns_keys]
            columns = [(dimension_label, 'text')] + [(label, 'monetary') for label in column_labels] \
                + [(self.env._("Total"), 'monetary')]
            model_cols = [group_by, *column_labels, 'total']
        else:
            columns = [(dimension_label, 'text'), (measure_label, 'monetary'), (self.env._("Share %"), 'percent')]
            model_cols = [group_by, measure, 'share_pct']
        period_label = self._ai_period_label(date_from, date_to)
        title = self.env._("%(measure)s by %(dimension)s", measure=measure_label, dimension=dimension_label)
        if then_by:
            title = self.env._("%(title)s and %(dimension)s", title=title,
                               dimension=then_by.replace('_', ' ').title())
        blocks = [self._ai_table('%s · %s' % (title, period_label), columns, rows)]
        chart_rows = model_rows[:12]
        if then_by:
            datasets = [(column_labels[index], [row[1 + index] for row in chart_rows])
                        for index in range(min(len(columns_keys), 6))]
        else:
            datasets = [(measure_label, [row[1] for row in chart_rows])]
        chart = self._ai_chart(arguments.get('chart'), title, [row[0] for row in chart_rows], datasets)
        if chart:
            blocks.append(chart)
        model = {'measure': measure, 'period': self._ai_iso(date_from, date_to), 'total': grand_total,
                 'cols': model_cols, **self._ai_compact_rows(model_rows)}
        if others:
            model['others'] = len(others)
        return {'model': model, 'blocks': blocks, 'label': blocks[0]['title'],
                'digest': self._ai_digest('%s %s' % (title, model['period']), model_rows)}

    @api.model
    def _ai_period_figures(self, date_from, date_to):
        revenue, expenses = self._ai_profit_figures(date_from, date_to)
        invoice_domain = [('state', '=', 'posted'), ('company_id', 'in', self.env.companies.ids),
                          ('invoice_date', '<=', date_to)]
        if date_from:
            invoice_domain.append(('invoice_date', '>=', date_from))
        sales = self._ai_sum('account.move', invoice_domain + [
            ('move_type', 'in', CUSTOMER_MOVE_TYPES)], 'amount_untaxed_signed')
        purchases = -self._ai_sum('account.move', invoice_domain + [
            ('move_type', 'in', VENDOR_MOVE_TYPES)], 'amount_untaxed_signed')
        invoices = self.env['account.move'].search_count(invoice_domain + [
            ('move_type', '=', 'out_invoice')])
        return {'revenue': revenue, 'expenses': expenses, 'profit': revenue - expenses,
                'sales': sales, 'purchases': purchases, 'invoices': invoices}

    def _ai_tool_compare_periods(self, arguments):
        a_from, a_to = self._ai_resolve_period({'period': arguments.get('period_a'),
                                                'date_from': arguments.get('a_from'),
                                                'date_to': arguments.get('a_to')})
        b_from, b_to = self._ai_resolve_period({'period': arguments.get('period_b'),
                                                'date_from': arguments.get('b_from'),
                                                'date_to': arguments.get('b_to')})
        figures_a = self._ai_period_figures(a_from, a_to)
        figures_b = self._ai_period_figures(b_from, b_to)
        labels = {'revenue': self.env._("Revenue"), 'expenses': self.env._("Expenses"),
                  'profit': self.env._("Net Profit"), 'sales': self.env._("Sales (untaxed)"),
                  'purchases': self.env._("Purchases (untaxed)")}
        label_a, label_b = self._ai_period_label(a_from, a_to), self._ai_period_label(b_from, b_to)
        rows, model_rows = [], []
        for key, label in labels.items():
            value_a, value_b = self._ai_round(figures_a[key]), self._ai_round(figures_b[key])
            row = [label, value_a, value_b, self._ai_round(value_a - value_b),
                   self._ai_delta(value_a, value_b)]
            rows.append({'cells': row, 'bold': key == 'profit'})
            model_rows.append([key, value_a, value_b, row[3], row[4]])
        table = self._ai_table(
            self.env._("%(a)s vs %(b)s", a=label_a, b=label_b),
            [(self.env._("Metric"), 'text'), (label_a, 'monetary'), (label_b, 'monetary'),
             (self.env._("Difference"), 'monetary'), (self.env._("Change %"), 'percent')], rows)
        blocks = [table]
        chart = self._ai_chart(arguments.get('chart'), table['title'],
                               [labels[key] for key in ('revenue', 'expenses', 'profit')],
                               [(label_a, [figures_a[key] for key in ('revenue', 'expenses', 'profit')]),
                                (label_b, [figures_b[key] for key in ('revenue', 'expenses', 'profit')])])
        if chart:
            blocks.append(chart)
        model = {'a': self._ai_iso(a_from, a_to), 'b': self._ai_iso(b_from, b_to),
                 'invoices_a': figures_a['invoices'], 'invoices_b': figures_b['invoices'],
                 'cols': ['metric', 'a', 'b', 'diff', 'change_pct'], 'rows': model_rows}
        return {'model': model, 'blocks': blocks, 'label': table['title'],
                'digest': self._ai_digest('compare %s vs %s' % (model['a'], model['b']), model_rows)}

    def _ai_tool_get_margins(self, arguments):
        group_by = arguments.get('group_by') or 'product'
        date_from, date_to = self._ai_resolve_period(arguments, default='this_year')
        limit = self._ai_limit(arguments)
        path = {'product': 'product_id', 'customer': 'partner_id',
                'product_category': 'product_id.categ_id'}.get(group_by)
        if not path:
            raise UserError(self.env._("Unknown grouping %s.", group_by))
        domain = self._ai_aml_domain(date_from, date_to) + [
            ('move_id.move_type', 'in', CUSTOMER_MOVE_TYPES), ('display_type', '=', 'product'),
            ('product_id', '!=', False)]
        groupby = [path, 'product_id', 'move_id.move_type'] if path != 'product_id' \
            else ['product_id', 'move_id.move_type']
        groups = self.env['account.move.line']._read_group(
            domain, groupby, ['balance:sum', 'quantity:sum'])
        revenue, cost = defaultdict(float), defaultdict(float)
        for row in groups:
            if path == 'product_id':
                product, move_type, balance, quantity = row
                key = product
            else:
                key, product, move_type, balance, quantity = row
            sign = -1 if move_type == 'out_refund' else 1
            revenue[key] += -balance
            cost[key] += sign * quantity * product.with_company(self.env.company).standard_price
        keys = sorted(revenue, key=lambda key: revenue[key], reverse=True)[:limit]
        rows, model_rows = [], []
        for key in keys:
            margin = revenue[key] - cost[key]
            pct = round(margin / revenue[key] * 100, 1) if revenue[key] else None
            values = [key.display_name if key else self.env._("Undefined"),
                      self._ai_round(revenue[key]), self._ai_round(cost[key]),
                      self._ai_round(margin), pct]
            rows.append({'cells': values})
            model_rows.append(values)
        total_revenue, total_cost = sum(revenue.values()), sum(cost.values())
        total_margin = total_revenue - total_cost
        total_pct = round(total_margin / total_revenue * 100, 1) if total_revenue else None
        rows.append({'cells': [self.env._("Total"), self._ai_round(total_revenue), self._ai_round(total_cost),
                               self._ai_round(total_margin), total_pct], 'bold': True})
        dimension_label = group_by.replace('_', ' ').title()
        title = self.env._("Gross Margin by %s", dimension_label)
        period_label = self._ai_period_label(date_from, date_to)
        blocks = [self._ai_table('%s · %s' % (title, period_label),
                                 [(dimension_label, 'text'), (self.env._("Revenue"), 'monetary'),
                                  (self.env._("Est. Cost"), 'monetary'), (self.env._("Margin"), 'monetary'),
                                  (self.env._("Margin %"), 'percent')], rows)]
        chart = self._ai_chart(arguments.get('chart'), title, [row[0] for row in model_rows],
                               [(self.env._("Margin"), [row[3] for row in model_rows])])
        if chart:
            blocks.append(chart)
        model = {'period': self._ai_iso(date_from, date_to), 'cost_basis': 'current product cost',
                 'total_margin_pct': total_pct, 'cols': [group_by, 'revenue', 'cost', 'margin', 'margin_pct'],
                 **self._ai_compact_rows(model_rows)}
        return {'model': model, 'blocks': blocks, 'label': blocks[0]['title'],
                'digest': self._ai_digest('margins %s' % model['period'], model_rows)}

    def _ai_tool_get_cash_forecast(self, arguments):
        granularity = arguments.get('granularity') if arguments.get('granularity') in ('week', 'month') \
            else 'week'
        try:
            periods = max(1, min(int(arguments.get('periods') or 8), 26))
        except (TypeError, ValueError):
            periods = 8
        today = fields.Date.context_today(self)
        opening = self._ai_sum('account.move.line', self._ai_aml_domain(
            False, today, ('asset_cash',)), 'balance')
        open_domain = [('parent_state', '=', 'posted'), ('company_id', 'in', self.env.companies.ids),
                       ('reconciled', '=', False)]
        flows = {}
        for kind, account_type in (('in', 'asset_receivable'), ('out', 'liability_payable')):
            series = self._ai_daily_series(
                'account.move.line', open_domain + [('account_id.account_type', '=', account_type)],
                'date_maturity', 'amount_residual:sum', granularity)
            flows[kind] = {bucket: abs(amount) for bucket, amount in series.items()}
        start = self._ai_bucket_start(today, granularity)
        step = relativedelta(weeks=1) if granularity == 'week' else relativedelta(months=1)
        overdue_in = sum(amount for bucket, amount in flows['in'].items() if bucket and bucket < start)
        overdue_out = sum(amount for bucket, amount in flows['out'].items() if bucket and bucket < start)
        balance = opening
        rows = [{'cells': [self.env._("Opening cash"), None, None, None, self._ai_round(opening)], 'bold': True},
                {'cells': [self.env._("Overdue"), self._ai_round(overdue_in), self._ai_round(overdue_out),
                           self._ai_round(overdue_in - overdue_out), None]}]
        model_rows, labels, balances = [], [], []
        bucket = start
        for _index in range(periods):
            inflow = flows['in'].get(bucket, 0.0)
            outflow = flows['out'].get(bucket, 0.0)
            balance += inflow - outflow
            label = self._ai_bucket_label(bucket, granularity)
            values = [label, self._ai_round(inflow), self._ai_round(outflow),
                      self._ai_round(inflow - outflow), self._ai_round(balance)]
            rows.append({'cells': values})
            model_rows.append(values)
            labels.append(label)
            balances.append(balance)
            bucket += step
        title = self.env._("Cash Forecast")
        blocks = []
        chart = self._ai_chart(arguments.get('chart') or 'line', self.env._("Projected cash balance"),
                               labels, [(self.env._("Projected balance"), balances)])
        if chart:
            blocks.append(chart)
        blocks.append(self._ai_table(
            '%s · %s' % (title, self.env._("by %s", granularity)),
            [(self.env._("Period"), 'text'), (self.env._("Expected In"), 'monetary'),
             (self.env._("Expected Out"), 'monetary'), (self.env._("Net"), 'monetary'),
             (self.env._("Projected Balance"), 'monetary')], rows))
        model = {'opening_cash': self._ai_round(opening), 'overdue_in': self._ai_round(overdue_in),
                 'overdue_out': self._ai_round(overdue_out),
                 'note': 'excludes overdue amounts, drafts and recurring entries',
                 'cols': [granularity, 'in', 'out', 'net', 'balance'], 'rows': model_rows}
        return {'model': model, 'blocks': blocks, 'label': title,
                'digest': self._ai_digest('cash forecast opening %s' % model['opening_cash'], model_rows)}

    def _ai_tool_get_ratios(self, arguments):
        date_from, date_to = self._ai_resolve_period(arguments, default='this_year')
        today = fields.Date.context_today(self)
        end = min(date_to, today)
        days = max((end - date_from).days + 1, 1) if date_from else 365
        Line = 'account.move.line'
        balance_domain = self._ai_aml_domain(False, date_to)
        receivables = self._ai_sum(Line, balance_domain + [('account_id.account_type', '=', 'asset_receivable')],
                                   'balance')
        payables = -self._ai_sum(Line, balance_domain + [('account_id.account_type', '=', 'liability_payable')],
                                 'balance')
        cash = self._ai_sum(Line, balance_domain + [('account_id.account_type', '=', 'asset_cash')], 'balance')
        current_assets = self._ai_sum(Line, balance_domain + [('account_id.account_type', 'in', (
            'asset_receivable', 'asset_cash', 'asset_current', 'asset_prepayments'))], 'balance')
        current_liabilities = -self._ai_sum(Line, balance_domain + [('account_id.account_type', 'in', (
            'liability_payable', 'liability_credit_card', 'liability_current'))], 'balance')
        invoice_domain = [('state', '=', 'posted'), ('company_id', 'in', self.env.companies.ids),
                          ('invoice_date', '<=', date_to)]
        if date_from:
            invoice_domain.append(('invoice_date', '>=', date_from))
        invoiced = self._ai_sum('account.move', invoice_domain + [
            ('move_type', 'in', CUSTOMER_MOVE_TYPES)], 'amount_total_signed')
        billed = -self._ai_sum('account.move', invoice_domain + [
            ('move_type', 'in', VENDOR_MOVE_TYPES)], 'amount_total_signed')
        revenue, expenses = self._ai_profit_figures(date_from, date_to)
        direct_cost = self._ai_sum(Line, self._ai_aml_domain(date_from, date_to, ('expense_direct_cost',)),
                                   'balance')

        def ratio(numerator, denominator, factor=1.0, digits=1):
            return round(numerator / denominator * factor, digits) if denominator else None

        figures = {
            'dso_days': ratio(receivables, invoiced, days),
            'dpo_days': ratio(payables, billed, days),
            'current_ratio': ratio(current_assets, current_liabilities, digits=2),
            'quick_ratio': ratio(cash + receivables, current_liabilities, digits=2),
            'gross_margin_pct': ratio(revenue - direct_cost, revenue, 100),
            'net_margin_pct': ratio(revenue - expenses, revenue, 100),
        }
        items = [
            (self.env._("Days Sales Outstanding"), figures['dso_days'], 'days'),
            (self.env._("Days Payable Outstanding"), figures['dpo_days'], 'days'),
            (self.env._("Current Ratio"), figures['current_ratio'], 'ratio'),
            (self.env._("Quick Ratio"), figures['quick_ratio'], 'ratio'),
            (self.env._("Gross Margin"), figures['gross_margin_pct'], 'percent'),
            (self.env._("Net Margin"), figures['net_margin_pct'], 'percent'),
        ]
        period_label = self._ai_period_label(date_from, date_to)
        block = {
            'type': 'kpis',
            'title': '%s · %s' % (self.env._("Financial Ratios"), period_label),
            'items': [{'label': label, 'value': value, 'type': kind, 'delta': None}
                      for label, value, kind in items],
            'currency_id': self.env.company.currency_id.id,
        }
        model = {'period': self._ai_iso(date_from, date_to), 'days': days, **figures}
        return {'model': model, 'blocks': [block], 'label': block['title'],
                'digest': 'ratios %s: %s' % (model['period'], ', '.join(
                    '%s %s' % (key, value) for key, value in figures.items()))}

    # ------------------------------------------------------------------
    # Detail lookups
    # ------------------------------------------------------------------
    def _ai_tool_get_payments(self, arguments):
        kind = arguments.get('kind') or 'all'
        status = arguments.get('status') or 'done'
        date_from, date_to = self._ai_resolve_period(arguments)
        domain = [('company_id', 'in', self.env.companies.ids), ('date', '<=', date_to)]
        if date_from:
            domain.append(('date', '>=', date_from))
        if kind != 'all':
            domain.append(('payment_type', '=', 'inbound' if kind == 'received' else 'outbound'))
        if status == 'done':
            domain.append(('state', 'in', ('paid', 'reconciled')))
        elif status == 'draft':
            domain.append(('state', '=', 'draft'))
        if arguments.get('partner'):
            partners = self._ai_find_partner(arguments['partner'])
            domain.append(('partner_id', 'child_of', partners.commercial_partner_id.ids))
        Payment = self.env['account.payment']
        payments = Payment.search(domain, order='date desc, id desc', limit=self._ai_limit(arguments))
        count = Payment.search_count(domain)
        received = self._ai_sum('account.payment', domain + [('payment_type', '=', 'inbound')],
                                'amount_company_currency_signed')
        sent = -self._ai_sum('account.payment', domain + [('payment_type', '=', 'outbound')],
                             'amount_company_currency_signed')
        states = dict(Payment._fields['state']._description_selection(self.env))
        rows, model_rows = [], []
        for payment in payments:
            values = [payment.name or '', str(payment.date or ''), payment.partner_id.display_name or '',
                      payment.journal_id.name, self._ai_round(payment.amount_company_currency_signed),
                      states.get(payment.state, payment.state)]
            rows.append({'cells': values, 'res_model': 'account.payment', 'res_id': payment.id})
            model_rows.append(values)
        period_label = self._ai_period_label(date_from, date_to)
        table = self._ai_table(
            '%s · %s (%s)' % (self.env._("Payments"), period_label, count),
            [(self.env._("Number"), 'text'), (self.env._("Date"), 'date'), (self.env._("Partner"), 'text'),
             (self.env._("Journal"), 'text'), (self.env._("Amount"), 'monetary'),
             (self.env._("Status"), 'text')], rows)
        model = {'period': self._ai_iso(date_from, date_to), 'count': count,
                 'received': self._ai_round(received), 'sent': self._ai_round(sent),
                 'cols': ['number', 'date', 'partner', 'journal', 'amount', 'status'],
                 **self._ai_compact_rows(model_rows)}
        return {'model': model, 'blocks': [table], 'label': table['title'],
                'digest': 'payments %s: %s, received %s, sent %s' % (
                    model['period'], count, model['received'], model['sent'])}

    def _ai_tool_search_journal_items(self, arguments):
        date_from, date_to = self._ai_resolve_period(arguments)
        domain = Domain(self._ai_aml_domain(date_from, date_to))
        if arguments.get('account'):
            term = arguments['account'].strip()
            accounts = self.env['account.account'].search(
                Domain('code', '=like', term + '%') | Domain('name', 'ilike', term))
            if not accounts:
                raise UserError(self.env._("No account matches '%s'.", term))
            domain &= Domain('account_id', 'in', accounts.ids)
        if arguments.get('partner'):
            partners = self._ai_find_partner(arguments['partner'])
            domain &= Domain('partner_id', 'child_of', partners.commercial_partner_id.ids)
        if arguments.get('journal'):
            term = arguments['journal'].strip()
            journals = self.env['account.journal'].search(
                Domain('code', '=ilike', term) | Domain('name', 'ilike', term))
            domain &= Domain('journal_id', 'in', journals.ids)
        if arguments.get('text'):
            term = arguments['text'].strip()
            domain &= Domain('name', 'ilike', term) | Domain('move_id.ref', 'ilike', term) \
                | Domain('move_id.name', 'ilike', term)
        if arguments.get('min_amount'):
            minimum = abs(arguments['min_amount'])
            domain &= Domain('debit', '>=', minimum) | Domain('credit', '>=', minimum)
        # 0 is how some models say "no maximum"; it would match nothing.
        if arguments.get('max_amount'):
            maximum = abs(arguments['max_amount'])
            domain &= Domain('debit', '<=', maximum) & Domain('credit', '<=', maximum)
        Line = self.env['account.move.line']
        lines = Line.search(domain, order='date desc, id desc', limit=self._ai_limit(arguments))
        count = Line.search_count(domain)
        debit = self._ai_sum('account.move.line', domain, 'debit')
        credit = self._ai_sum('account.move.line', domain, 'credit')
        rows, model_rows = [], []
        for line in lines:
            values = [str(line.date), line.move_id.name, line.journal_id.code,
                      line.account_id.code or line.account_id.name, line.partner_id.display_name or '',
                      (line.name or '')[:60], self._ai_round(line.debit), self._ai_round(line.credit)]
            rows.append({'cells': values, 'res_model': 'account.move', 'res_id': line.move_id.id})
            model_rows.append(values)
        rows.append({'cells': [self.env._("Total (%s items)", count), '', '', '', '', '',
                               self._ai_round(debit), self._ai_round(credit)], 'bold': True})
        period_label = self._ai_period_label(date_from, date_to)
        table = self._ai_table(
            '%s · %s' % (self.env._("Journal Items"), period_label),
            [(self.env._("Date"), 'date'), (self.env._("Entry"), 'text'), (self.env._("Journal"), 'text'),
             (self.env._("Account"), 'text'), (self.env._("Partner"), 'text'), (self.env._("Label"), 'text'),
             (self.env._("Debit"), 'monetary'), (self.env._("Credit"), 'monetary')], rows)
        model = {'period': self._ai_iso(date_from, date_to), 'count': count,
                 'debit': self._ai_round(debit), 'credit': self._ai_round(credit),
                 'cols': ['date', 'entry', 'journal', 'account', 'partner', 'label', 'debit', 'credit'],
                 **self._ai_compact_rows(model_rows)}
        return {'model': model, 'blocks': [table], 'label': table['title'],
                'digest': self._ai_digest('journal items %s: %s' % (model['period'], count), model_rows, size=3)}

    def _ai_tool_get_invoice_details(self, arguments):
        number = (arguments.get('number') or '').strip()
        if not number:
            raise UserError(self.env._("Please give an invoice number."))
        Move = self.env['account.move']
        domain = [('company_id', 'in', self.env.companies.ids),
                  ('move_type', 'in', CUSTOMER_MOVE_TYPES + VENDOR_MOVE_TYPES)]
        moves = Move.search(domain + [('name', '=ilike', number)], limit=1) \
            or Move.search(domain + [('name', 'ilike', number)], limit=6)
        if not moves:
            raise UserError(self.env._("No invoice matches '%s'.", number))
        if len(moves) > 1:
            names = moves.mapped('name')
            return {'model': {'ambiguous': True, 'candidates': names},
                    'digest': 'invoice ambiguous: %s' % ', '.join(names)}
        move = moves
        states = dict(Move._fields['payment_state']._description_selection(self.env))
        summary = {
            'type': 'kpis',
            'title': '%s · %s · %s' % (move.name, move.partner_id.display_name or '',
                                       states.get(move.payment_state, move.payment_state)),
            'items': [{'label': label, 'value': self._ai_round(value), 'delta': None}
                      for label, value in ((self.env._("Untaxed"), move.amount_untaxed),
                                           (self.env._("Taxes"), move.amount_tax),
                                           (self.env._("Total"), move.amount_total),
                                           (self.env._("Amount Due"), move.amount_residual))],
            'currency_id': move.currency_id.id,
            'res_model': 'account.move',
            'res_id': move.id,
        }
        rows, model_rows = [], []
        for line in move.invoice_line_ids.filtered(lambda line: line.display_type == 'product'):
            values = [line.product_id.display_name or line.name or '', self._ai_round(line.quantity),
                      self._ai_round(line.price_unit), self._ai_round(line.discount),
                      ', '.join(line.tax_ids.mapped('name')), self._ai_round(line.price_subtotal)]
            rows.append({'cells': values})
            model_rows.append(values)
        table = self._ai_table(self.env._("Invoice Lines"),
                               [(self.env._("Product"), 'text'), (self.env._("Quantity"), 'number'),
                                (self.env._("Unit Price"), 'monetary'), (self.env._("Discount %"), 'percent'),
                                (self.env._("Taxes"), 'text'), (self.env._("Subtotal"), 'monetary')], rows)
        table['currency_id'] = move.currency_id.id
        model = {'number': move.name, 'partner': move.partner_id.display_name, 'date': str(move.invoice_date or ''),
                 'due': str(move.invoice_date_due or ''), 'currency': move.currency_id.name,
                 'state': move.state, 'payment_state': move.payment_state,
                 'untaxed': self._ai_round(move.amount_untaxed), 'tax': self._ai_round(move.amount_tax),
                 'total': self._ai_round(move.amount_total), 'due_amount': self._ai_round(move.amount_residual),
                 'cols': ['product', 'qty', 'price', 'discount', 'taxes', 'subtotal'],
                 **self._ai_compact_rows(model_rows)}
        return {'model': model, 'blocks': [summary, table], 'label': move.name,
                'digest': 'invoice %s %s total %s due %s' % (
                    move.name, model['partner'], model['total'], model['due_amount'])}

    def _ai_tool_get_unreconciled_bank_lines(self, arguments):
        domain = [('company_id', 'in', self.env.companies.ids), ('is_reconciled', '=', False),
                  ('state', '=', 'posted')]
        if arguments.get('journal'):
            term = arguments['journal'].strip()
            journals = self.env['account.journal'].search(
                [('type', 'in', ('bank', 'cash', 'credit')), ('name', 'ilike', term)])
            domain.append(('journal_id', 'in', journals.ids))
        Line = self.env['account.bank.statement.line']
        lines = Line.search(domain, order='date desc, id desc', limit=self._ai_limit(arguments))
        per_journal = Line._read_group(domain, ['journal_id'], ['__count', 'amount:sum'])
        rows, model_rows = [], []
        for line in lines:
            values = [str(line.date), line.journal_id.name, line.payment_ref or '',
                      line.partner_id.display_name or line.partner_name or '', self._ai_round(line.amount)]
            rows.append({'cells': values, 'res_model': 'account.bank.statement.line', 'res_id': line.id})
            model_rows.append(values)
        count = sum(group[1] for group in per_journal)
        total = self._ai_round(sum(group[2] for group in per_journal))
        rows.append({'cells': [self.env._("Total (%s lines)", count), '', '', '', total], 'bold': True})
        table = self._ai_table(
            self.env._("Unreconciled Bank Lines (%s)", count),
            [(self.env._("Date"), 'date'), (self.env._("Journal"), 'text'), (self.env._("Label"), 'text'),
             (self.env._("Partner"), 'text'), (self.env._("Amount"), 'monetary')], rows)
        model = {'count': count, 'total': total,
                 'per_journal': [[journal.name, journal_count, self._ai_round(amount)]
                                 for journal, journal_count, amount in per_journal],
                 'cols': ['date', 'journal', 'label', 'partner', 'amount'], **self._ai_compact_rows(model_rows)}
        return {'model': model, 'blocks': [table], 'label': table['title'],
                'digest': 'unreconciled bank lines: %s, total %s' % (count, total)}

    # ------------------------------------------------------------------
    # Generic data queries
    # ------------------------------------------------------------------
    @api.model
    def _ai_is_secret(self, name):
        name = name.lower()
        return any(marker in name for marker in SECRET_FIELD_MARKERS)

    @api.model
    def _ai_queryable_model(self, model_name):
        """Model the AI may query, after access checks (read)."""
        model_name = (model_name or '').strip().lower()
        Model = self.env.get(model_name)
        if Model is None or model_name.startswith(DENIED_MODEL_PREFIXES) \
                or Model._abstract or Model._transient:
            raise UserError(self.env._(
                "Model '%s' is not available; use describe_data to find the right one.", model_name))
        Model.check_access('read')
        return Model

    @api.model
    def _ai_check_path(self, Model, path):
        """Validate a dotted field path: every hop exists, is not secret and
        does not read inside a technical or security model (a field may
        point to a user, e.g. the salesperson, but not read its login)."""
        current = Model
        for name in path.split(':')[0].split('.'):
            if self._ai_is_secret(name) or name not in current._fields \
                    or current._name.startswith(DENIED_MODEL_PREFIXES):
                raise UserError(self.env._("Unknown or forbidden field %(field)s on %(model)s.",
                                           field=name, model=current._name))
            field = current._fields[name]
            if field.relational:
                current = self.env[field.comodel_name]
        return path

    @api.model
    def _ai_path_field(self, Model, path):
        """Last field of a validated dotted path."""
        self._ai_check_path(Model, path)
        current, field = Model, None
        for name in path.split(':')[0].split('.'):
            field = current._fields[name]
            if field.relational:
                current = self.env[field.comodel_name]
        return field

    @api.model
    def _ai_parse_domain(self, Model, raw):
        """Domain from the AI: JSON (or a Python literal), a single condition
        or a list of them. Every field path is checked (also inside ``any``
        sub-domains) and operators are limited to DOMAIN_OPERATORS."""
        if not raw:
            return []
        domain = parse_json(raw) if isinstance(raw, str) else raw
        if domain is None:
            raise UserError(self.env._("The domain is not valid JSON: %s", str(raw)[:200]))
        return Domain(self._ai_check_domain(Model, domain))

    @api.model
    def _ai_check_domain(self, Model, domain, depth=0):
        if isinstance(domain, tuple):
            domain = list(domain)
        if not isinstance(domain, list):
            raise UserError(self.env._("The domain must be a JSON list of conditions."))
        # A single condition sent without the outer list.
        if len(domain) == 3 and isinstance(domain[0], str) and isinstance(domain[1], str) \
                and domain[0] not in ('&', '|', '!'):
            domain = [domain]
        if len(domain) > MAX_DOMAIN_ITEMS or depth > 2:
            raise UserError(self.env._("The domain is too long (at most %s conditions).", MAX_DOMAIN_ITEMS))
        result = []
        for item in domain:
            if isinstance(item, str) and item in ('&', '|', '!'):
                result.append(item)
                continue
            if not isinstance(item, (list, tuple)) or len(item) != 3 or not isinstance(item[0], str):
                raise UserError(self.env._("Invalid domain condition %s: use [field, operator, value].",
                                           json.dumps(item, default=str)[:200]))
            path, operator, value = item[0].strip(), str(item[1]).strip().lower(), item[2]
            operator = OPERATOR_ALIASES.get(operator, operator)
            if operator not in DOMAIN_OPERATORS:
                raise UserError(self.env._("Operator %(operator)s is not allowed. Use one of: %(operators)s.",
                                           operator=item[1], operators=' '.join(DOMAIN_OPERATORS)))
            field = self._ai_path_field(Model, path)
            if operator in ('any', 'not any'):
                if not field.relational:
                    raise UserError(self.env._("%s needs a relational field.", operator))
                value = parse_json(value) if isinstance(value, str) else value
                value = self._ai_check_domain(self.env[field.comodel_name], value, depth + 1)
            elif operator in ('in', 'not in'):
                values = value if isinstance(value, (list, tuple)) else [value]
                value = [self._ai_domain_value(field, item) for item in values]
            elif operator not in ('child_of', 'parent_of') and 'like' not in operator:
                value = self._ai_domain_value(field, value)
            result.append((path, operator, value))
        return result

    @api.model
    def _ai_domain_value(self, field, value):
        """Domain value checked against the field type before any SQL runs:
        a wrong type is an error message for the AI, not a failed query."""
        if value is None or value is False:
            return False
        if isinstance(value, (list, dict)):
            raise UserError(self.env._("%s: use the in / not in operators for lists of values.", field.name))
        try:
            if field.type in ('integer', 'float', 'monetary') or (field.relational and not isinstance(value, str)):
                number = coerce_number(value, field.name)
                if (field.type == 'integer' or field.relational) and (
                        number != int(number) or abs(number) > MAX_INTEGER):
                    raise ArgumentError(self.env._("%s expects a whole number.", field.name))
                return number
            if field.type == 'boolean':
                return coerce_boolean(value, field.name)
            if field.type == 'date':
                return fields.Date.to_string(self._ai_parse_date(value))
            if field.type == 'datetime':
                text = str(value).strip()
                if re.fullmatch(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})?', text):
                    moment = datetime.fromisoformat(text.replace('Z', '+00:00'))
                    if moment.tzinfo:
                        moment = moment.astimezone(ZoneInfo('UTC')).replace(tzinfo=None)
                    return fields.Datetime.to_string(moment)
                return fields.Date.to_string(self._ai_parse_date(value))
        except ArgumentError as error:
            raise UserError(str(error)) from error
        return value if isinstance(value, (str, int, float, bool)) else str(value)
    @api.model
    def _ai_query_value(self, value, field=None):
        if isinstance(value, models.BaseModel):
            return ', '.join(value.mapped('display_name'))[:120]
        if field is not None and field.type == 'selection' and value:
            return dict(field._description_selection(self.env)).get(value, value)
        if isinstance(value, float):
            return self._ai_round(value)
        if isinstance(value, str):
            return value[:200]
        if value is False or value is None:
            return ''
        return value if isinstance(value, (int, bool)) else str(value)

    @api.model
    def _ai_column_type(self, field):
        if field.type == 'monetary':
            return 'monetary'
        if field.type in ('integer', 'float'):
            return 'number'
        if field.type in ('date', 'datetime'):
            return 'date'
        return 'text'

    @api.model
    def _ai_period_domain(self, Model, domain, arguments):
        """Add the period filter on ``date_field``. Datetime fields are
        filtered on whole local days (user time zone), e.g. a product created
        on Oct 31 at 18:00 is "created in October"."""
        if not arguments.get('period'):
            return domain
        date_field = arguments.get('date_field') or ('date' if 'date' in Model._fields else 'create_date')
        self._ai_check_path(Model, date_field)
        field = Model._fields[date_field]
        if field.type not in ('date', 'datetime'):
            raise UserError(self.env._("date_field %s is not a date field.", date_field))
        date_from, date_to = self._ai_resolve_period(arguments)
        if field.type == 'date':
            period_domain = Domain(date_field, '<=', date_to)
            if date_from:
                period_domain &= Domain(date_field, '>=', date_from)
        else:
            zone = ZoneInfo(self.env.context.get('tz') or self.env.user.tz or 'UTC')

            def to_utc(day):
                local = datetime.combine(day, dt_time.min).replace(tzinfo=zone)
                return local.astimezone(ZoneInfo('UTC')).replace(tzinfo=None)

            period_domain = Domain(date_field, '<', to_utc(date_to + timedelta(days=1)))
            if date_from:
                period_domain &= Domain(date_field, '>=', to_utc(date_from))
        return Domain(domain) & period_domain

    @api.model
    def _ai_related_domain(self, Model, domain, related):
        """Restrict ``domain`` to records that are (``with``) or are not
        (``without``) referenced by ``related['model']`` through its many2one
        ``related['field']``. The referenced ids come from one grouped query
        run with the user's access rights."""
        if not related:
            return domain
        if isinstance(related, str):
            related = json.loads(related)
        if not isinstance(related, dict):
            raise UserError(self.env._("related must be an object."))
        mode = related.get('mode') or 'without'
        if mode not in ('with', 'without'):
            raise UserError(self.env._("related.mode must be 'with' or 'without'."))
        if not related.get('model') or not related.get('field'):
            raise UserError(self.env._("related needs both model and field (or leave related out)."))
        Related = self._ai_queryable_model(related.get('model'))
        field_name = (related.get('field') or '').strip()
        self._ai_check_path(Related, field_name)
        field = Related._fields[field_name]
        if field.type != 'many2one' or field.comodel_name != Model._name:
            raise UserError(self.env._(
                "related.field must be a many2one of %(related)s pointing to %(model)s.",
                related=Related._name, model=Model._name))
        # Without the "!= False" filter, a NULL in the list would make
        # "not in" match nothing.
        related_domain = Domain(self._ai_parse_domain(Related, related.get('domain'))) \
            & Domain(field_name, '!=', False)
        referenced = [record.id for (record,) in Related._read_group(related_domain, [field_name])]
        return Domain(domain) & Domain('id', 'in' if mode == 'with' else 'not in', referenced)

    @api.model
    def _ai_group_spec(self, Model, spec):
        """``field`` or ``date_field:granularity``; date fields default to
        months and granularities are given in plain words (``monthly``)."""
        path, _sep, granularity = spec.partition(':')
        field = self._ai_path_field(Model, path.strip())
        if field.type in ('date', 'datetime'):
            granularity = resolve_enum(granularity or 'month', TIME_DIMENSIONS, 'group_by granularity')
            return '%s:%s' % (path.strip(), granularity)
        if granularity:
            raise UserError(self.env._("%s is not a date field: group it without ':granularity'.", path))
        return path.strip()

    @api.model
    def _ai_aggregate_spec(self, Model, aggregate):
        """``count`` or ``field:function``, from what models write:
        ``sum(amount_total)``, ``sum:amount_total``, ``amount_total:total``."""
        text = (aggregate or 'count').strip()
        if text.lower() in ('count', '__count', 'count(*)', 'count(id)', 'id:count', 'count:id', 'records',
                            'number', 'count:*', '*:count'):
            return 'count'
        match = re.fullmatch(r'(\w+)\s*\(\s*([\w.]+)\s*\)', text)
        if match:
            function, field_name = match.groups()
        elif ':' in text:
            field_name, function = (part.strip() for part in text.split(':', 1))
            if field_name.lower() in QUERY_AGGREGATES or field_name.lower() in AGGREGATE_ALIASES:
                field_name, function = function, field_name
        else:
            raise UserError(self.env._("Aggregate must be count or field:%s, e.g. amount_total:sum.",
                                       '|'.join(QUERY_AGGREGATES)))
        function = function.lower()
        function = function if function in QUERY_AGGREGATES else AGGREGATE_ALIASES.get(function)
        if not function:
            raise UserError(self.env._("Aggregate must be count or field:%s, e.g. amount_total:sum.",
                                       '|'.join(QUERY_AGGREGATES)))
        if '.' in field_name:
            raise UserError(self.env._("Aggregate a field of the model itself, not %s.", field_name))
        field = self._ai_path_field(Model, field_name)
        if function != 'count_distinct' and field.type not in ('integer', 'float', 'monetary') \
                and not (function in ('min', 'max') and field.type in ('date', 'datetime')):
            raise UserError(self.env._("%(field)s is not numeric: %(function)s is not possible.",
                                       field=field_name, function=function))
        return '%s:%s' % (field_name, function)

    def _ai_tool_query_records(self, arguments):
        Model = self._ai_queryable_model(arguments.get('model'))
        domain = self._ai_parse_domain(Model, arguments.get('domain'))
        limit = self._ai_limit(arguments)
        group_by = [self._ai_group_spec(Model, spec) for spec in (arguments.get('group_by') or [])[:2]]
        aggregate = self._ai_aggregate_spec(Model, arguments.get('aggregate'))
        model_label = Model._description or Model._name
        domain = self._ai_period_domain(Model, domain, arguments)
        domain = self._ai_related_domain(Model, domain, arguments.get('related'))
        count = Model.search_count(domain)
        display = arguments.get('display') is not False

        if group_by:
            if aggregate == 'count':
                aggregate_spec, value_type = '__count', 'number'
            else:
                field_name, _sep, function = aggregate.partition(':')
                aggregate_spec = aggregate
                value_type = self._ai_column_type(Model._fields[field_name]) \
                    if function != 'count_distinct' else 'number'
            time_grouped = any(':' in spec for spec in group_by[:1])
            groups = Model._read_group(domain, group_by, [aggregate_spec],
                                       order=None if time_grouped else '%s desc' % aggregate_spec,
                                       limit=None if time_grouped else limit)
            fields_by_spec = [Model._fields.get(spec.split(':')[0].split('.')[0]) for spec in group_by]
            rows, model_rows = [], []
            for group in groups[:MAX_ROWS * 4]:
                labels = [self._ai_group_label(value, spec.split(':')[1]) if ':' in spec
                          else (self._ai_query_value(value, field) or self.env._("Undefined"))
                          for value, spec, field in zip(group[:-1], group_by, fields_by_spec)]
                value = self._ai_round(group[-1]) if isinstance(group[-1], float) else group[-1]
                rows.append({'cells': [*labels, value]})
                model_rows.append([*labels, value])
            value_label = self.env._("Count") if aggregate == 'count' else aggregate
            columns = [(spec, 'text') for spec in group_by] + [(value_label, value_type)]
            title = self.env._("%(model)s by %(groups)s", model=model_label, groups=', '.join(group_by))
            blocks = [self._ai_table(title, columns, rows)]
            if len(group_by) == 1:
                chart = self._ai_chart(arguments.get('chart'), title, [row[0] for row in model_rows[:20]],
                                       [(value_label, [row[1] for row in model_rows[:20]])])
                if chart:
                    blocks.append(chart)
            model = {'model': Model._name, 'matching_records': count, 'cols': [*group_by, aggregate],
                     **self._ai_compact_rows(model_rows)}
            group_ids = [group[0].id for group in groups[:len(model['rows'])]
                         if isinstance(group[0], models.BaseModel) and group[0]]
            if group_ids:
                model['group_ids'] = group_ids
            return {'model': model, 'blocks': blocks if display else [], 'label': title,
                    'digest': self._ai_digest('%s (%s records)' % (title, count), model_rows)}

        names = [self._ai_check_path(Model, name) for name in (arguments.get('fields') or [])
                 if '.' not in name][:MAX_QUERY_FIELDS] or ['display_name']
        fields_list = [Model._fields[name] for name in names
                       if Model._fields[name].type not in ('binary', 'image', 'json', 'properties')]
        order = (arguments.get('order') or '').strip() or None
        if order:
            for term in order.split(','):
                self._ai_check_path(Model, term.strip().split(' ')[0])
        records = Model.search(domain, order=order, limit=limit)
        rows, model_rows = [], []
        for record in records:
            values = [self._ai_query_value(record[field.name], field) for field in fields_list]
            rows.append({'cells': values, 'res_model': Model._name, 'res_id': record.id})
            model_rows.append(values)
        columns = [(field.string or field.name, self._ai_column_type(field)) for field in fields_list]
        title = self.env._("%(model)s (%(count)s)", model=model_label, count=count)
        table = self._ai_table(title, columns, rows)
        model = {'model': Model._name, 'count': count, 'cols': [field.name for field in fields_list],
                 **self._ai_compact_rows(model_rows)}
        model['ids'] = records.ids[:len(model['rows'])]
        return {'model': model, 'blocks': [table] if model_rows and display else [], 'label': title,
                'digest': self._ai_digest('%s: %s records' % (Model._name, count), model_rows, size=3)}

    def _ai_tool_describe_data(self, arguments):
        search = (arguments.get('search') or '').strip().lower()[:100]
        model_name = (arguments.get('model') or '').strip()
        if model_name:
            Model = self._ai_queryable_model(model_name)
            fields_info = []
            # fields_get only returns the fields the user is allowed to read.
            described = Model.fields_get(attributes=['type', 'string', 'relation', 'searchable'])
            for name, info in sorted(described.items()):
                if self._ai_is_secret(name) or info['type'] in ('binary', 'image') \
                        or not info.get('searchable'):
                    continue
                if search and search not in name.lower() and search not in (info.get('string') or '').lower():
                    continue
                spec = '%s:%s' % (name, info['type'])
                if info.get('relation'):
                    spec += ':%s' % info['relation']
                fields_info.append(spec)
            model = {'model': Model._name, 'description': Model._description,
                     'fields': fields_info[:80], 'more_fields': max(len(fields_info) - 80, 0)}
            return {'model': model, 'label': Model._description or Model._name,
                    'digest': 'fields of %s' % Model._name}
        matches = []
        # ir.model is only read to list names; each model is then checked
        # against the user's own read access.
        for model in self.env['ir.model'].sudo().search([('transient', '=', False)], order='model'):
            if model.model.startswith(DENIED_MODEL_PREFIXES) or model.model not in self.env:
                continue
            if search and search not in model.model.lower() and search not in (model.name or '').lower():
                continue
            if not self.env[model.model].has_access('read'):
                continue
            matches.append([model.model, model.name])
            if len(matches) >= 40:
                break
        return {'model': {'models': matches}, 'label': self.env._("Models matching %s", search or '*'),
                'digest': 'models for %s' % search}

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------
    @api.model
    def _ai_dump(self, value):
        """Compact JSON for the AI: no spaces, dates as strings."""
        return json.dumps(value, separators=(',', ':'), ensure_ascii=False, default=str)
