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
"""Normalisation of the tool-call arguments sent by AI models.

Models do not always follow the declared JSON schema. Depending on the
provider and the model they:

* send every optional parameter, empty (``""``, ``[]``, ``{}``, ``null``),
* send numbers and booleans as strings, integers as floats (``10.0``),
* write enum values in another case or as synonyms (``"Customers"``,
  ``"monthly"``, ``"column"``),
* use parameter names of their own (``start_date`` for ``date_from``),
* send a JSON array where a JSON string is declared (domains) or a comma
  separated string where an array is declared.

``normalize_arguments`` turns such calls into arguments that match the
schema exactly, so tools never see an unexpected type or value, or raises an
``ArgumentError`` whose message tells the model how to fix its call.
Unknown parameters are rejected instead of ignored: a filter silently dropped
would give a wrong figure, an error only costs one more step.
"""
import ast
import calendar
import json
import re
from datetime import date, datetime, timedelta

from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta


class ArgumentError(ValueError):
    """Arguments that cannot be understood; the message is meant for the AI."""


# Declared parameter -> names models use for it instead. An alias is only
# applied when the tool does not declare a parameter of that name itself.
PARAMETER_ALIASES = {
    'date_from': ('start_date', 'from_date', 'date_start', 'start', 'from', 'since', 'begin',
                  'begin_date', 'datefrom', 'period_start'),
    'date_to': ('end_date', 'to_date', 'date_end', 'end', 'to', 'until', 'dateto', 'period_end'),
    'period': ('date_range', 'time_period', 'timeframe', 'time_frame', 'time_range', 'range',
               'date_filter', 'period_name'),
    'partner': ('partner_name', 'partner_id', 'customer', 'customer_name', 'vendor', 'vendor_name',
                'supplier', 'supplier_name', 'contact'),
    'limit': ('top', 'top_n', 'n', 'max_results', 'max_rows', 'rows', 'size', 'max_records'),
    'kind': ('type', 'direction', 'side', 'partner_type', 'invoice_type', 'move_type'),
    'group_by': ('groupby', 'group', 'dimension', 'by', 'grouping'),
    'then_by': ('second_group_by', 'split_by', 'subgroup', 'sub_group_by', 'and_by', 'group_by_2'),
    'model': ('model_name', 'res_model', 'table', 'object'),
    'domain': ('filter', 'filters', 'conditions', 'where', 'criteria'),
    'fields': ('columns', 'field_names', 'select'),
    'number': ('invoice_number', 'invoice', 'invoice_name', 'name', 'reference', 'ref', 'bill_number'),
    'order': ('order_by', 'sort', 'sort_by', 'sorting'),
    'measure': ('metric', 'value'),
    'metric': ('measure', 'value'),
    'granularity': ('interval', 'frequency', 'bucket', 'group_by', 'by', 'step'),
    'as_of': ('date', 'at', 'as_of_date', 'on', 'at_date', 'date_to', 'end_date'),
    'chart': ('chart_type', 'graph', 'graph_type', 'visualization', 'plot'),
    'search': ('keyword', 'query', 'q', 'term', 'name'),
    'text': ('label', 'keyword', 'query', 'q', 'reference', 'ref', 'search'),
    'account': ('account_code', 'account_name', 'account_id'),
    'journal': ('journal_name', 'journal_code', 'journal_id', 'bank'),
    'date_field': ('date_column', 'datetime_field', 'filter_field', 'date_filter_field'),
    'aggregate': ('aggregation', 'agg', 'operation'),
    'periods': ('horizon', 'buckets', 'num_periods', 'number_of_periods', 'count'),
    'detail': ('level', 'detail_level', 'details'),
    'compare': ('comparison', 'compare_to', 'compare_with', 'vs'),
    'min_amount': ('amount_min', 'minimum', 'min', 'min_value', 'amount_gte'),
    'max_amount': ('amount_max', 'maximum', 'max_value', 'amount_lte'),
    'status': ('state', 'payment_state', 'payment_status', 'invoice_status'),
    'display': ('show', 'visible', 'display_table'),
}

# Enum synonyms: normalised raw value -> candidates, the first one declared
# by the parameter wins. Exact values and singular/plural forms are matched
# before these.
ENUM_SYNONYMS = {
    # partners and directions
    'client': ('customer', 'sale', 'received', 'receivable'),
    'customers': ('customer', 'sale', 'received', 'receivable', 'partner'),
    'customer': ('customer', 'sale', 'received', 'receivable', 'partner'),
    'sales': ('sales', 'sale', 'customer', 'received', 'revenue', 'amount'),
    'sale': ('sale', 'sales', 'customer', 'received'),
    'sold': ('sale', 'sales', 'customer'),
    'income': ('revenue', 'sale', 'received'),
    'receivable': ('receivable', 'customer', 'received'),
    'ar': ('receivable', 'customer'),
    'supplier': ('vendor', 'purchase', 'sent', 'payable', 'partner'),
    'suppliers': ('vendor', 'purchase', 'sent', 'payable', 'partner'),
    'vendor': ('vendor', 'purchase', 'sent', 'payable', 'partner'),
    'vendors': ('vendor', 'purchase', 'sent', 'payable', 'partner'),
    'purchases': ('purchases', 'purchase', 'vendor', 'sent', 'expenses'),
    'purchase': ('purchase', 'purchases', 'vendor', 'sent'),
    'bought': ('purchase', 'purchases', 'vendor'),
    'bills': ('vendor', 'purchase'),
    'bill': ('vendor', 'purchase'),
    'invoices': ('customer', 'sale'),
    'payable': ('payable', 'vendor', 'sent'),
    'ap': ('payable', 'vendor'),
    'inbound': ('received',), 'incoming': ('received',), 'in': ('received', 'with'),
    'receipts': ('received',), 'collected': ('received',),
    'outbound': ('sent',), 'outgoing': ('sent',), 'out': ('sent',), 'made': ('sent',),
    'partner': ('partner', 'customer'), 'partners': ('partner', 'customer'), 'contact': ('partner',),
    # statuses
    'unpaid': ('open',), 'outstanding': ('open',), 'not_paid': ('open',), 'due': ('open', 'due_asc'),
    'pending': ('open', 'draft'), 'partial': ('open',), 'partially_paid': ('open',), 'open': ('open',),
    'late': ('overdue',), 'past_due': ('overdue',), 'overdue_only': ('overdue',),
    'settled': ('paid', 'done'), 'in_payment': ('paid', 'done'), 'paid': ('paid', 'done'),
    'posted': ('done', 'all'), 'confirmed': ('done',), 'validated': ('done',), 'completed': ('done',),
    'reconciled': ('done', 'paid'), 'done': ('done', 'paid'),
    'unposted': ('draft',), 'draft': ('draft',),
    'any': ('all',), 'both': ('all',), 'everything': ('all',), 'every': ('all',),
    # charts
    'no': ('none',), 'false': ('none',), 'off': ('none',), 'table': ('none',), 'no_chart': ('none',),
    'null': ('none',), 'n/a': ('none',),
    'true': ('bar',), 'yes': ('bar',), 'chart': ('bar',), 'graph': ('bar',),
    'column': ('bar',), 'columns': ('bar',), 'bar_chart': ('bar',), 'histogram': ('bar',),
    'bars': ('bar',), 'barchart': ('bar',), 'column_chart': ('bar',),
    'line_chart': ('line',), 'area': ('line',), 'linechart': ('line',), 'lines': ('line',),
    'trend': ('line',), 'timeseries': ('line',),
    'donut': ('pie',), 'doughnut': ('pie',), 'pie_chart': ('pie',), 'piechart': ('pie',),
    # comparisons
    'prior_period': ('previous_period',), 'last_period': ('previous_period',),
    'previous': ('previous_period',), 'prev': ('previous_period',), 'prior': ('previous_period',),
    'mom': ('previous_period',), 'period_over_period': ('previous_period',),
    'prior_year': ('previous_year',), 'last_year': ('previous_year',), 'yoy': ('previous_year',),
    'year_over_year': ('previous_year',), 'same_period_last_year': ('previous_year',),
    'previous_month': ('previous_period',), 'last_month': ('previous_period',),
    'prior_month': ('previous_period',), 'previous_quarter': ('previous_period',),
    'last_quarter': ('previous_period',),
    # detail levels
    'short': ('summary',), 'brief': ('summary',), 'condensed': ('summary',), 'total': ('summary',),
    'totals': ('summary',),
    'detailed': ('accounts',), 'full': ('accounts',), 'account': ('accounts', 'account'),
    'by_account': ('accounts',),
    # metrics
    'value': ('amount',), 'amount_total': ('amount',), 'money': ('amount',), 'turnover': ('amount', 'revenue'),
    'qty': ('quantity',), 'units': ('quantity',), 'volume': ('quantity',), 'quantities': ('quantity',),
    'expense': ('expenses',), 'costs': ('expenses',), 'cost': ('expenses',), 'spending': ('expenses',),
    'net_profit': ('profit',), 'net_income': ('profit',), 'earnings': ('profit',), 'margin': ('profit',),
    'revenue': ('revenue', 'amount', 'sales'), 'revenues': ('revenue', 'amount', 'sales'),
    # granularity
    'daily': ('day',), 'days': ('day',), 'weekly': ('week',), 'weeks': ('week',),
    'monthly': ('month',), 'months': ('month',), 'quarterly': ('quarter',), 'quarters': ('quarter',),
    'yearly': ('year',), 'annual': ('year',), 'annually': ('year',), 'years': ('year',),
    # dimensions
    'category': ('product_category',), 'categories': ('product_category',),
    'product_categories': ('product_category',), 'categ': ('product_category',), 'categ_id': ('product_category',),
    'products': ('product',), 'product_id': ('product',), 'items': ('product',), 'item': ('product',),
    'partner_id': ('partner',), 'account_id': ('account',), 'journal_id': ('journal',),
    'accounts': ('account', 'accounts'), 'gl_account': ('account',), 'journals': ('journal',),
    'salesman': ('salesperson',), 'sales_person': ('salesperson',), 'salespeople': ('salesperson',),
    'seller': ('salesperson',), 'user': ('salesperson',), 'invoice_user_id': ('salesperson',),
    'countries': ('country',), 'country_id': ('country',), 'region': ('country',),
    'analytic': ('analytic_account',), 'analytic_accounts': ('analytic_account',),
    'cost_center': ('analytic_account',), 'project': ('analytic_account',),
    # orders
    'amount': ('amount', 'amount_desc'), 'largest': ('amount_desc',), 'biggest': ('amount_desc',),
    'highest': ('amount_desc',), 'top': ('amount_desc',), 'amount_descending': ('amount_desc',),
    'date': ('date_desc',), 'latest': ('date_desc',), 'recent': ('date_desc',), 'newest': ('date_desc',),
    'date_descending': ('date_desc',), 'due_date': ('due_asc',), 'oldest_due': ('due_asc',),
    'due_ascending': ('due_asc',),
    # related filter
    'has': ('with',), 'having': ('with',), 'linked': ('with',), 'used': ('with',), 'exists': ('with',),
    'not': ('without',), 'no_related': ('without',), 'never': ('without',), 'missing': ('without',),
    'lacking': ('without',), 'not_in': ('without',), 'unused': ('without',),
}

TRUE_STRINGS = {'true', 'yes', 'y', '1', 'on'}
FALSE_STRINGS = {'false', 'no', 'n', '0', 'off', 'none', 'null'}
MONTHS = {name.lower(): index for index, name in enumerate(calendar.month_name) if name}
MONTHS.update({name.lower(): index for index, name in enumerate(calendar.month_abbr) if name})
MONTHS['sept'] = 9

# Period keywords models write instead of the documented ones.
PERIOD_ALIASES = {
    'current_month': 'this_month', 'month': 'this_month', 'mtd': 'this_month',
    'month_to_date': 'this_month', 'this_month_to_date': 'this_month',
    'previous_month': 'last_month', 'prior_month': 'last_month', 'past_month': 'last_month',
    'current_week': 'this_week', 'week': 'this_week', 'wtd': 'this_week', 'week_to_date': 'this_week',
    'previous_week': 'last_week', 'prior_week': 'last_week', 'past_week': 'last_week',
    'current_quarter': 'this_quarter', 'quarter': 'this_quarter', 'qtd': 'this_quarter',
    'quarter_to_date': 'this_quarter', 'previous_quarter': 'last_quarter',
    'prior_quarter': 'last_quarter', 'past_quarter': 'last_quarter',
    'current_year': 'this_year', 'year': 'this_year', 'this_fiscal_year': 'this_year',
    'current_fiscal_year': 'this_year', 'fiscal_year': 'this_year', 'fy': 'this_year',
    'previous_year': 'last_year', 'prior_year': 'last_year', 'last_fiscal_year': 'last_year',
    'previous_fiscal_year': 'last_year', 'past_year': 'last_year',
    'ytd': 'year_to_date', 'fytd': 'year_to_date', 'fiscal_year_to_date': 'year_to_date',
    'all': 'all_time', 'ever': 'all_time', 'lifetime': 'all_time', 'alltime': 'all_time',
    'since_inception': 'all_time', 'overall': 'all_time', 'to_date': 'all_time', 'any': 'all_time',
    'everything': 'all_time', 'full_history': 'all_time',
    'ttm': 'last_12_months', 'ltm': 'last_12_months', 'trailing_12_months': 'last_12_months',
    'rolling_12_months': 'last_12_months', 'past_12_months': 'last_12_months',
    'last_twelve_months': 'last_12_months',
    'past_30_days': 'last_30_days', 'last_month_30_days': 'last_30_days', 'past_90_days': 'last_90_days',
    'now': 'today', 'current_day': 'today', 'previous_day': 'yesterday',
    'custom_range': 'custom', 'date_range': 'custom', 'between': 'custom', 'range': 'custom',
    'specific': 'custom', 'dates': 'custom', 'manual': 'custom',
}
NUMBER_WORDS = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7,
                'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12, 'thirty': 30,
                'sixty': 60, 'ninety': 90}


def normalize_key(value):
    """Lower case, words joined by underscores: ``"Previous Year"`` ->
    ``previous_year``."""
    return re.sub(r'[\s\-]+', '_', str(value).strip().lower()).strip('_')


# ----------------------------------------------------------------------
# Schema driven coercion
# ----------------------------------------------------------------------
def normalize_arguments(schema, arguments):
    """Arguments matching ``schema`` (a JSON object schema), with empty
    values removed; raises ArgumentError when they cannot be understood."""
    arguments = _parse_object(arguments, 'arguments')
    properties = schema.get('properties') or {}
    result = {}
    unknown = []
    for raw_key, value in arguments.items():
        key = _resolve_key(str(raw_key), properties)
        if key is None:
            if not _is_empty(value):
                unknown.append(str(raw_key))
            continue
        try:
            value = _coerce(value, properties[key], key)
        except ArgumentError:
            raise
        except (TypeError, ValueError) as error:
            raise ArgumentError('%s: %s' % (key, error)) from error
        # A declared name wins over an alias of it.
        if _is_empty(value) or (key in result and key != raw_key):
            continue
        result[key] = value
    if unknown:
        raise ArgumentError('Unknown parameter(s) %s. Parameters of this tool: %s.' % (
            ', '.join(sorted(unknown)), ', '.join(sorted(properties)) or 'none'))
    return result


def check_required(schema, arguments):
    missing = [key for key in schema.get('required') or () if _is_empty(arguments.get(key))]
    if missing:
        hints = []
        for key in missing:
            enum = (schema.get('properties') or {}).get(key, {}).get('enum')
            hints.append('%s (%s)' % (key, ' | '.join(enum)) if enum else key)
        raise ArgumentError('Missing required parameter(s): %s.' % ', '.join(hints))


def _is_empty(value):
    return value is None or (isinstance(value, (str, list, dict, tuple)) and not (
        value.strip() if isinstance(value, str) else value))


def _resolve_key(key, properties):
    if key in properties:
        return key
    normalized = normalize_key(key)
    if normalized in properties:
        return normalized
    for target, aliases in PARAMETER_ALIASES.items():
        if target in properties and normalized in aliases and normalized not in properties:
            return target
    return None


def _parse_object(value, name):
    if isinstance(value, dict):
        return value
    if _is_empty(value):
        return {}
    if isinstance(value, str):
        parsed = parse_json(value)
        if isinstance(parsed, dict):
            return parsed
    raise ArgumentError('%s must be a JSON object.' % name)


def parse_json(text):
    """JSON, or a Python literal (models sometimes write ``'x'``, ``True``,
    ``None``); None when it is neither."""
    text = text.strip()
    for loader in (json.loads, ast.literal_eval):
        try:
            value = loader(text)
        except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
            continue
        # A JSON string holding JSON (double encoding).
        if isinstance(value, str) and value.strip()[:1] in ('[', '{'):
            inner = parse_json(value)
            return inner if inner is not None else value
        return value
    return None


def _coerce(value, schema, key):
    if _is_empty(value):
        return None
    kind = schema.get('type')
    if kind == 'object':
        return _coerce_object(value, schema, key)
    if kind == 'array':
        return _coerce_array(value, schema, key)
    if kind == 'integer':
        return _coerce_integer(value, key)
    if kind == 'number':
        return coerce_number(value, key)
    if kind == 'boolean':
        return coerce_boolean(value, key)
    value = _coerce_string(value, key)
    if schema.get('enum'):
        return resolve_enum(value, schema['enum'], key)
    return value


def _coerce_object(value, schema, key):
    value = _parse_object(value, key)
    properties = schema.get('properties')
    if not properties:
        return value
    unknown = [name for name, item in value.items() if name not in properties and not _is_empty(item)]
    if unknown:
        raise ArgumentError('Unknown key(s) %s in %s. Keys: %s.' % (
            ', '.join(sorted(map(str, unknown))), key, ', '.join(sorted(properties))))
    result = {}
    for name, item in value.items():
        if name in properties:
            item = _coerce(item, properties[name], '%s.%s' % (key, name))
            if not _is_empty(item):
                result[name] = item
    # An object left with only its mode is not set (e.g. a "related"
    # filter sent with empty model and field).
    if not set(result) - {'mode'}:
        return None
    return result


def _coerce_array(value, schema, key):
    if isinstance(value, str):
        parsed = parse_json(value) if value.strip()[:1] == '[' else None
        value = parsed if isinstance(parsed, list) else [part for part in value.split(',')]
    elif isinstance(value, tuple):
        value = list(value)
    elif not isinstance(value, list):
        value = [value]
    item_schema = schema.get('items') or {}
    items = [_coerce(item, item_schema, key) for item in value]
    return [item for item in items if not _is_empty(item)]


def _coerce_integer(value, key):
    number = coerce_number(value, key)
    if number != int(number):
        raise ArgumentError('%s must be a whole number, got %s.' % (key, value))
    return int(number)


def coerce_number(value, key):
    if isinstance(value, bool):
        raise ArgumentError('%s must be a number, got %s.' % (key, value))
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        # Currency symbols or codes, thousands separators, spaces and a
        # percent sign are dropped: "$ 1,250.50", "1250 EUR", "15%".
        text = re.sub(r'[\s,$€£¥₹%]|\b(?:usd|eur|gbp|inr|aed|sar)\b', '', str(value), flags=re.IGNORECASE)
        multiplier = 1
        if re.fullmatch(r'[-+]?[\d.]+[kKmM]', text):
            multiplier = 1000 if text[-1] in 'kK' else 1000000
            text = text[:-1]
        try:
            number = float(text) * multiplier
        except ValueError:
            raise ArgumentError('%s must be a number, got %r.' % (key, value)) from None
    if number != number or number in (float('inf'), float('-inf')):
        raise ArgumentError('%s must be a finite number.' % key)
    return int(number) if number == int(number) and abs(number) < 2 ** 53 else number


def coerce_boolean(value, key):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    text = str(value).strip().lower()
    if text in TRUE_STRINGS:
        return True
    if text in FALSE_STRINGS:
        return False
    raise ArgumentError('%s must be true or false, got %r.' % (key, value))


def _coerce_string(value, key):
    if isinstance(value, str):
        # NUL characters are refused by PostgreSQL.
        return value.replace('\x00', '').strip()
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        return str(int(value)) if isinstance(value, float) and value == int(value) else str(value)
    if isinstance(value, (list, tuple)) and len(value) == 1 and not isinstance(value[0], (list, dict)):
        return _coerce_string(value[0], key)
    if isinstance(value, (list, tuple, dict)):
        # e.g. a domain sent as an actual array: keep it as the JSON text
        # the parameter declares.
        return json.dumps(value)
    raise ArgumentError('%s must be a string.' % key)


def resolve_enum(value, allowed, key):
    """Allowed value matching ``value`` (exact, case, separators, plural
    or a synonym); raises ArgumentError listing the allowed values."""
    if value in allowed:
        return value
    raw = normalize_key(value)
    candidates = [raw, raw.replace('_', ''), raw.rstrip('s'), raw + 's', raw.removesuffix('es')]
    candidates += list(ENUM_SYNONYMS.get(raw, ())) + list(ENUM_SYNONYMS.get(raw.rstrip('s'), ()))
    for candidate in candidates:
        if candidate in allowed:
            return candidate
    raise ArgumentError('%s must be one of: %s (got %r).' % (key, ', '.join(allowed), value))


# ----------------------------------------------------------------------
# Dates and periods
# ----------------------------------------------------------------------
def parse_date(value, end=False, dayfirst=True):
    """A date from what models write: ISO dates or datetimes, ``YYYY-MM``
    and ``YYYY`` (first or last day with ``end``), or a written date such as
    ``"Oct 31, 2026"`` (``dayfirst`` decides ``01/10/2026``)."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        value = str(int(value))
    if not isinstance(value, str) or not value.strip():
        raise ArgumentError('Invalid date %r, expected YYYY-MM-DD.' % (value,))
    text = value.strip()
    match = re.fullmatch(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?:[T ].*)?', text)
    if match:
        return _make_date(*map(int, match.groups()), text=text)
    match = re.fullmatch(r'(\d{4})(\d{2})(\d{2})', text)
    if match:
        return _make_date(*map(int, match.groups()), text=text)
    match = re.fullmatch(r'(\d{4})[-/.](\d{1,2})', text)
    if match:
        year, month = map(int, match.groups())
        _make_date(year, month, 1, text=text)
        return date(year, month, calendar.monthrange(year, month)[1] if end else 1)
    match = re.fullmatch(r'(\d{4})', text)
    if match:
        year = int(text)
        return date(year, 12, 31) if end else date(year, 1, 1)
    try:
        first = date_parser.parse(text, dayfirst=dayfirst, default=datetime(2000, 1, 1))
        second = date_parser.parse(text, dayfirst=dayfirst, default=datetime(2000, 1, 28))
    except (ValueError, OverflowError, TypeError):
        raise ArgumentError('Invalid date %r, expected YYYY-MM-DD.' % text) from None
    if first.year == 2000 and not re.search(r'2000', text):
        # No year written: the most recent such date is meant.
        raise ArgumentError('Invalid date %r: give the year, as YYYY-MM-DD.' % text)
    if first.day != second.day and end:
        # Month without a day, e.g. "October 2026": last day for an end date.
        return date(first.year, first.month, calendar.monthrange(first.year, first.month)[1])
    return first.date()


def _make_date(year, month, day, text=''):
    try:
        return date(year, month, day)
    except ValueError:
        raise ArgumentError('Invalid date %r, expected YYYY-MM-DD.' % text) from None


def resolve_period_text(value, today, periods):
    """``(keyword, date_from, date_to)`` for a period written by a model:
    a documented keyword of ``periods`` (dates None), or a period in words
    resolved to dates (keyword ``custom``): ``october``, ``Oct 2026``,
    ``Q3 2026``, ``2025``, ``last 7 days``, ``2026-10``... Raises
    ArgumentError when it means nothing."""
    key = normalize_key(value)
    if key in periods:
        return key, None, None
    if key in PERIOD_ALIASES:
        return PERIOD_ALIASES[key], None, None
    words = re.sub(r'[_,]+', ' ', key).strip()
    words = re.sub(r'\b(the|of|in|for|during)\b', ' ', words)
    words = re.sub(r'\s+', ' ', words).strip()

    # last / past / previous N days|weeks|months|years
    match = re.fullmatch(r'(?:last|past|previous|trailing|rolling)\s*(\d+|[a-z]+)?\s*'
                         r'(day|week|month|quarter|year)s?', words)
    if match:
        count_text, unit = match.groups()
        count = 1 if not count_text else (
            int(count_text) if count_text.isdigit() else NUMBER_WORDS.get(count_text))
        if count and not count_text:
            return {'day': 'yesterday', 'week': 'last_week', 'month': 'last_month',
                    'quarter': 'last_quarter', 'year': 'last_year'}[unit], None, None
        if count:
            return ('custom', *_trailing_period(today, count, unit))

    # this / current / next words are covered by the aliases; quarters:
    match = re.fullmatch(r'q([1-4])(?:\s*(?:fy)?\s*(\d{4}))?', words) \
        or re.fullmatch(r'(?:fy\s*)?(\d{4})\s*q([1-4])', words)
    if match:
        groups = match.groups()
        if words.startswith('q'):
            quarter, year = int(groups[0]), int(groups[1]) if groups[1] else None
        else:
            year, quarter = int(groups[0]), int(groups[1])
        if year is None:
            year = today.year if (quarter - 1) * 3 + 1 <= today.month else today.year - 1
        start = date(year, (quarter - 1) * 3 + 1, 1)
        return 'custom', start, start + relativedelta(months=3, days=-1)

    # month names, with or without a year
    match = re.fullmatch(r'([a-z]+)\s*(\d{4})?', words) or re.fullmatch(r'(\d{4})\s*([a-z]+)', words)
    if match:
        first, second = match.groups()
        name, year = (first, second) if not first.isdigit() else (second, first)
        if name in MONTHS:
            month = MONTHS[name]
            year = int(year) if year else (today.year if month <= today.month else today.year - 1)
            return 'custom', date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])

    # a year, a month or a single day written as a date
    match = re.fullmatch(r'(?:fy\s*)?(\d{4})', words)
    if match:
        year = int(match.group(1))
        return 'custom', date(year, 1, 1), date(year, 12, 31)
    try:
        start, stop = parse_date(value, end=False), parse_date(value, end=True)
    except ArgumentError:
        pass
    else:
        return 'custom', start, stop
    raise ArgumentError('Unknown period %r. Use one of: %s; or custom with date_from/date_to '
                        '(YYYY-MM-DD).' % (value, ', '.join(periods)))


def _trailing_period(today, count, unit):
    if unit == 'day':
        return today - timedelta(days=count - 1), today
    if unit == 'week':
        return today - timedelta(days=7 * count - 1), today
    if unit == 'year':
        return today - relativedelta(years=count) + timedelta(days=1), today
    # Whole calendar months, like the documented last_12_months.
    months = count * (3 if unit == 'quarter' else 1)
    return (today - relativedelta(months=months - 1)).replace(day=1), today
