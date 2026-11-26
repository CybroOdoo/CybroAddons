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
"""Engine of the dynamic reports.

A dynamic report is a small abstract model inheriting
``account.dynamic.report``. It declares its filters and columns and returns
its lines; the figures come from the kit's report computations, called with
the same context the report wizards used (see ``_report_context``).

Everything the browser sends is rebuilt by ``_normalize_options``; the screen,
the PDF and the XLSX all come from ``get_report(options)``.

Line format::

    {'id': str, 'name': str, 'level': int, 'columns': [values],
     'unfoldable': bool, 'unfolded': bool, 'class': str (optional)}

``class``: ``'total'`` (grand total) and ``'main'`` (main section) are bold
on a grey band, ``'section'`` (sub-section, sub-total) is bold. ``style``
(optional, financial reports): the line's "Financial Report Style" ('1' to
'6'), which overrides the font.
"""
import ast
import csv
import io
import json
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import date_utils
from odoo.tools.misc import format_date, format_datetime, formatLang

from .report_company import (get_report_branches, get_report_company,
                             get_report_journal_domain)
from .report_xlsx_mixin import write_xlsx_table

DATE_PRESETS = ('this_month', 'this_quarter', 'this_year', 'last_month',
                'last_quarter', 'last_year', 'custom')
# Reports "as of a date": the end of these periods.
SINGLE_DATE_PRESETS = ('today', 'last_month', 'last_quarter', 'last_year',
                       'custom')



# Amount units of the report screen and exports: key -> (divisor, decimals
# (None: the currency's), suffix, XLSX number format of the positive part).
AMOUNT_UNITS = {
    'full': (1, None, '', '#,##0.00'),
    'int': (1, 0, '', '#,##0'),
    'k': (1000, 1, 'K', '#,##0.0,"K"'),
    'm': (1000000, 1, 'M', '#,##0.0,,"M"'),
}

class AccountDynamicReport(models.AbstractModel):
    _name = 'account.dynamic.report'
    _description = 'Dynamic Accounting Report'

    # The /xlsx_report controller streams the workbook of these models.
    _xlsx_report_allowed = True
    # Marks the models the generic PDF may print.
    _dynamic_report = True
    # Filters shown by the screen; extended by each report.
    _filters = ('date', 'target_move', 'journals')
    # Comparison periods are offered when True.
    _comparison = False
    # Columns by period (month / quarter) instead of one period (RI 3.2)
    _columns_by = False
    # 'range' (start and end date) or 'single' (as of a date).
    _date_mode = 'range'


    # ------------------------------------------------------------------
    # To implement in each report
    # ------------------------------------------------------------------
    def _report_title(self):
        return self._description

    def _columns(self, options):
        """Column headers: list of ``{'name', 'type'}``; ``type`` is
        ``'monetary'`` or ``'text'``. The line name is the first column and
        is not listed."""
        return []

    def _option_defs(self):
        """Extra options of the report, shown under "Options" and checked
        by ``_normalize_report_options``: list of ``{'key', 'label', 'type',
        'default'}``; ``type`` is ``'bool'``, ``'select'`` (with ``values``:
        ``{value: label}``) or ``'number'`` (with ``min`` / ``max``).
        Values are a dict: the translation export reads the keys of a list
        of ``(value, _(label))`` pairs as terms too."""
        return []

    def _account_domain(self):
        """Accounts offered by the Accounts filter."""
        return []

    def _report_journal_domain(self, company):
        """Journals offered by the Journals filter."""
        return get_report_journal_domain(company)

    def _lines(self, options):
        """Top level lines (see the module docstring)."""
        return []

    def _child_lines(self, options, line_id):
        """Lines shown under ``line_id`` when it is unfolded."""
        return []

    def _line_action(self, options, line_id):
        """Action opened when a line is clicked, or False."""
        return self._open_journal_item(line_id)

    def _open_journal_item(self, line_id):
        """Journal entry of a journal item line (id ``aml_<id>``)."""
        if not line_id.startswith('aml_'):
            return False
        line = self.env['account.move.line'].browse(
            int(line_id.split('_')[1])).exists()
        return line and {
            'type': 'ir.actions.act_window', 'res_model': 'account.move',
            'res_id': line.move_id.id, 'views': [(False, 'form')],
            'target': 'current'}

    # option key -> journal item field, for drill-down domains
    _kit_filter_fields = (('journal_ids', 'journal_id'),
                          ('partner_ids', 'partner_id'),
                          ('analytic_ids', 'analytic_distribution'))

    def _kit_filter_domain(self, options, keys=None):
        """Journal item domain of the chosen journals / partners / analytic
        accounts (only ``keys`` when given)."""
        return [(field, 'in', options[key]) for key, field in self._kit_filter_fields
                if (keys is None or key in keys) and options.get(key)]

    def _states(self, options):
        return ['posted'] if options['target_move'] == 'posted' \
            else ['draft', 'posted']

    # ------------------------------------------------------------------
    # Options
    # ------------------------------------------------------------------
    def _date_range(self, company, preset, date_from=None, date_to=None):
        """Dates of a preset; the year presets follow the company's fiscal
        year."""
        today = fields.Date.context_today(self)
        if self._date_mode == 'single':
            if preset == 'custom':
                date_to = fields.Date.to_date(date_to)
                if not date_to:
                    raise UserError(_("Set a date."))
                return False, date_to
            if preset == 'today':
                return False, today
            return False, self._period_end(company, preset, today)
        if preset == 'custom':
            date_from = fields.Date.to_date(date_from)
            date_to = fields.Date.to_date(date_to)
            if not date_from or not date_to:
                raise UserError(_("Set a start and an end date."))
            if date_from > date_to:
                raise UserError(_("The start date is after the end date."))
            return date_from, date_to
        if preset.startswith('last_'):
            unit = preset[5:]
            ref = {'month': today - relativedelta(months=1),
                   'quarter': today - relativedelta(months=3),
                   'year': company.compute_fiscalyear_dates(
                       today)['date_from'] - timedelta(days=1)}[unit]
        else:
            unit = preset[5:]
            ref = today
        if unit == 'year':
            dates = company.compute_fiscalyear_dates(ref)
            return dates['date_from'], dates['date_to']
        return date_utils.start_of(ref, unit), date_utils.end_of(ref, unit)

    @staticmethod
    def _period_end(company, preset, today):
        """End of last month / quarter / fiscal year (single date mode)."""
        unit = preset[5:]
        if unit == 'year':
            return company.compute_fiscalyear_dates(today)['date_from'] \
                - timedelta(days=1)
        return date_utils.start_of(today, unit) - timedelta(days=1)

    def _comparison_periods(self, company, options):
        """Earlier periods to compare with: ``[(date_from, date_to, label)]``,
        most recent first. ``previous`` shifts by the period length (a month,
        a quarter, a fiscal year, or the same number of days); ``last_year``
        takes the same dates one year earlier."""
        cmp = options['comparison']
        date_from, date_to = options['date_from'], options['date_to']
        preset = options['date_preset']
        periods = []
        for _i in range(cmp['periods']):
            if cmp['type'] == 'last_year':
                date_from -= relativedelta(years=1)
                date_to -= relativedelta(years=1)
            elif preset.endswith('_year'):
                fy = company.compute_fiscalyear_dates(
                    date_from - timedelta(days=1))
                date_from, date_to = fy['date_from'], fy['date_to']
            elif preset.endswith('_quarter'):
                date_from = date_utils.start_of(
                    date_from - relativedelta(months=3), 'quarter')
                date_to = date_utils.end_of(date_from, 'quarter')
            elif preset.endswith('_month'):
                date_from = date_utils.start_of(
                    date_from - relativedelta(months=1), 'month')
                date_to = date_utils.end_of(date_from, 'month')
            else:
                length = date_to - date_from
                date_to = date_from - timedelta(days=1)
                date_from = date_to - length
            periods.append((date_from, date_to, '%s - %s' % (
                fields.Date.to_string(date_from),
                fields.Date.to_string(date_to))))
        return periods

    def _kit_heading(self, options, company):
        """Statement heading of the screen (RI 1.5), under the report name:
        the period in words and what the extra columns compare."""
        long_date = lambda day: format_date(self.env, day, date_format='d MMMM yyyy')
        if options['date_from']:
            period = '%s – %s' % (long_date(options['date_from']),
                                  long_date(options['date_to']))
        else:
            period = _("As of %s", long_date(options['date_to']))
        if options['columns_by']:
            period = _("%(period)s, by quarter", period=period) \
                if options['columns_by'] == 'quarter' \
                else _("%(period)s, by month", period=period)
        elif options['comparison']['periods']:
            period = _("%(period)s, compared with %(count)s earlier period(s)",
                       period=period, count=options['comparison']['periods'])
        return {'period': period}

    def _kit_ledger_action(self, options, account, initial_balance):
        """The General Ledger of one account, unfolded, for the period,
        journals and posted / all entries of ``options``."""
        return {
            'type': 'ir.actions.client',
            'tag': 'kit_dynamic_report',
            'name': _("General Ledger"),
            'params': {
                'model': 'account.dynamic.report.general_ledger',
                'options': {
                    'company_id': options['company_id'],
                    'date_preset': 'custom',
                    'date_from': fields.Date.to_string(options['date_from']),
                    'date_to': fields.Date.to_string(options['date_to']),
                    'target_move': options['target_move'],
                    'journal_ids': options['journal_ids'],
                    'account_ids': [account.id],
                    'unfolded': ['account_%s' % account.id],
                    'initial_balance': initial_balance,
                },
            },
        }

    def _kit_period_columns(self, company, options):
        """Columns by period: the report period cut into months or quarters
        from its start date: ``[(date_from, date_to, label)]``, at most 24."""
        start, end = options['date_from'], options['date_to']
        if not options['columns_by'] or not start:
            return []
        months = 3 if options['columns_by'] == 'quarter' else 1
        periods = []
        while start <= end:
            stop = min(start + relativedelta(months=months, days=-1), end)
            label = format_date(self.env, start, date_format='MMM yyyy') \
                if months == 1 else '%s – %s' % (
                    format_date(self.env, start, date_format='MMM'),
                    format_date(self.env, stop, date_format='MMM yyyy'))
            periods.append((start, stop, label))
            if len(periods) > 24:
                raise UserError(_(
                    "Too many columns: at most 24 periods. Choose By quarter "
                    "or a shorter period."))
            start = stop + timedelta(days=1)
        return periods

    def _kit_period_column_defs(self, periods):
        """Column headers of the periods, with their dates (a click on an
        amount opens that period)."""
        return [{'name': label, 'type': 'monetary',
                 'date_from': fields.Date.to_string(date_from),
                 'date_to': fields.Date.to_string(date_to)}
                for date_from, date_to, label in periods]

    def _normalize_options(self, options):
        """Rebuild the options from what the browser sent: only values the
        user may use are kept, everything else gets a default."""
        options = dict(options or {})
        company = get_report_company(self.env, {
            'company_id': options.get('company_id')})
        if company not in self.env.companies:
            company = self.env.company
        preset = options.get('date_preset')
        if self._date_mode == 'single':
            if preset not in SINGLE_DATE_PRESETS:
                preset = 'today'
        elif preset not in DATE_PRESETS:
            preset = 'this_year'
        date_from, date_to = self._date_range(
            company, preset, options.get('date_from'), options.get('date_to'))
        journals = self.env['account.journal'].search(
            self._report_journal_domain(company))
        selected = [j for j in options.get('journal_ids') or []
                    if isinstance(j, int) and j in journals.ids]
        cmp = options.get('comparison') or {}
        try:
            n_periods = min(max(int(cmp.get('periods') or 0), 0), 12)
        except (TypeError, ValueError):
            n_periods = 0
        res = {
            'company_id': company.id,
            'date_preset': preset,
            'date_from': date_from,
            'date_to': date_to,
            'target_move': 'all' if options.get('target_move') == 'all'
            else 'posted',
            'journal_ids': selected,
            'comparison': {
                'periods': n_periods if self._comparison else 0,
                'type': 'last_year' if cmp.get('type') == 'last_year'
                else 'previous',
            },
            'unfolded': [str(i) for i in options.get('unfolded') or []],
            'unfold_all': bool(options.get('unfold_all')),
            # "$" in every amount, or plain amounts and the currency once
            'currency_symbol': bool(options.get('currency_symbol')),
            # statement heading (company, title, period) above the table
            'show_heading': bool(options.get('show_heading', True)),
            # one column per month / quarter of the period (no comparison)
            'columns_by': options.get('columns_by')
            if self._columns_by and options.get('columns_by') in ('month', 'quarter')
            else '',
            # amounts as they are, without decimals, in thousands or millions
            'amount_unit': options.get('amount_unit')
            if options.get('amount_unit') in AMOUNT_UNITS else 'full',
            'search': (options.get('search') or '').strip()[:100],
            'partner_ids': self._readable_ids(
                'res.partner', options.get('partner_ids'))
            if 'partners' in self._filters else [],
            'analytic_ids': self._readable_ids(
                'account.analytic.account', options.get('analytic_ids'))
            if 'analytic' in self._filters else [],
            'account_ids': self._readable_ids(
                'account.account', options.get('account_ids'))
            if 'accounts' in self._filters else [],
        }
        res.update(self._normalize_report_options(options))
        if res['columns_by']:
            res['comparison']['periods'] = 0
        return res

    def _readable_ids(self, model, ids):
        """Ids of records the user may read (others are dropped)."""
        ids = [i for i in ids or [] if isinstance(i, int)]
        return self.env[model].search([('id', 'in', ids)]).ids if ids else []

    def _normalize_report_options(self, options):
        """Check the report's own options against ``_option_defs``."""
        res = {}
        for definition in self._option_defs():
            key, default = definition['key'], definition['default']
            value = options.get(key, default)
            if definition['type'] == 'bool':
                value = bool(value)
            elif definition['type'] == 'select':
                if value not in dict(definition['values']):
                    value = default
            else:
                try:
                    value = min(max(int(value), definition.get('min', 0)),
                                definition.get('max', 9999))
                except (TypeError, ValueError):
                    value = default
            res[key] = value
        return res

    def _report_context(self, options, date_from=None, date_to=None):
        """Context of the kit's report computations (same keys as the
        wizards' ``_build_contexts``)."""
        date_from = options['date_from'] if date_from is None else date_from
        ctx = {
            'journal_ids': options['journal_ids'] or False,
            'state': options['target_move'],
            'date_from': date_from,
            'date_to': options['date_to'] if date_to is None else date_to,
            'strict_range': bool(date_from),
            'company_id': options['company_id'],
        }
        if options.get('partner_ids'):
            ctx['partner_ids'] = self.env['res.partner'].browse(
                options['partner_ids'])
        if options.get('analytic_ids'):
            ctx['analytic_account_ids'] = options['analytic_ids']
        if options.get('account_ids'):
            ctx['account_ids'] = self.env['account.account'].browse(
                options['account_ids'])
        return ctx

    # ------------------------------------------------------------------
    # Public API (screen, PDF, XLSX)
    # ------------------------------------------------------------------
    def _company_env(self, options):
        """Run under the report company: account codes and amounts are
        company-dependent (P1.7)."""
        company = self.env['res.company'].browse(options['company_id'])
        return self.with_company(company)

    def _report_notice(self, options):
        """Message of the report shown above its lines, if any."""
        return False

    @api.model
    def get_report(self, options=None):
        """Everything the screen (and the exports) need."""
        self.env['account.move.line'].check_access('read')
        # The kit's computations read journal items with SQL.
        self.env.flush_all()
        options = self._normalize_options(options)
        report = self._company_env(options)
        company = report.env.company
        lines = report._lines(options)
        expanded = []
        for line in lines:
            expanded.append(line)
            if line.get('unfoldable') and (
                    options['unfold_all'] or line['id'] in options['unfolded']):
                line['unfolded'] = True
                expanded += report._child_lines(options, line['id'])
        if options['search']:
            expanded = report._search_lines(expanded, options['search'])
        journals = report.env['account.journal'].search(
            report._report_journal_domain(company))
        covered = get_report_branches(company)
        others = self.env.companies - covered
        notices = [_("This report covers %(companies)s only. Not "
                     "included: %(others)s.",
                     companies=', '.join(covered.mapped('name')),
                     others=', '.join(others.mapped('name')))
                   if others else False, report._report_notice(options)]
        return {
            'title': report._report_title(),
            'options': options,
            'filters': list(self._filters),
            'option_defs': [dict(d, values=list(dict(d['values']).items()))
                            if 'values' in d else d
                            for d in report._option_defs()],
            'account_domain': report._account_domain(),
            'date_mode': self._date_mode,
            'notice': ' '.join(filter(None, notices)) or False,
            'comparison': self._comparison,
            'columns_by_allowed': self._columns_by,
            'columns': report._columns(options),
            'lines': expanded,
            'currency_id': company.currency_id.id,
            'currency_name': company.currency_id.name,
            'company_name': company.name,
            'branches': get_report_branches(company).mapped('name'),
            'heading': report._kit_heading(options, company),
            'journals': [{'id': j.id, 'name': j.name, 'code': j.code}
                         for j in journals],
        }

    @staticmethod
    def _search_lines(lines, text):
        """Keep the lines whose name contains ``text``, with their parent
        line and the total lines."""
        text = text.lower()
        kept, parent = [], None
        for line in lines:
            if line.get('level', 0) == 0:
                parent = line
            if text in (line.get('name') or '').lower() \
                    or line.get('class') == 'total':
                if parent is not None and parent is not line \
                        and parent not in kept:
                    kept.append(parent)
                kept.append(line)
        return kept

    @api.model
    def get_lines(self, options, line_id):
        """Children of one line, when it is unfolded on the screen."""
        self.env['account.move.line'].check_access('read')
        self.env.flush_all()
        options = self._normalize_options(options)
        return self._company_env(options)._child_lines(options, str(line_id))

    @api.model
    def action_open_line(self, options, line_id):
        """Drill down from a line (journal items, journal entry...)."""
        self.env['account.move.line'].check_access('read')
        options = self._normalize_options(options)
        return self._company_env(options)._line_action(options, str(line_id))

    @api.model
    def action_export_pdf(self, options):
        options = self._normalize_options(options)
        return self.env.ref(
            'base_accounting_kit.action_report_kit_statement').report_action(
            None, data={'model': self._name, 'options': self._json(options)},
            # own page header: no document layout to configure first
            config=False)

    @api.model
    def action_export_xlsx(self, options):
        options = self._normalize_options(options)
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {
                'model': self._name,
                'options': json.dumps(self._json(options)),
                'output_format': 'xlsx',
                'report_name': self._export_filename(options),
            },
        }

    @api.model
    def action_export_csv(self, options):
        """CSV of the report (same lines and columns as the XLSX, plain
        exact amounts), through the kit's export controller."""
        action = self.action_export_xlsx(options)
        action['data']['output_format'] = 'csv'
        return action

    @api.model
    def _export_filename(self, options):
        """File name of the PDF and XLSX (without extension): the report
        title and its period."""
        options = self._normalize_options(options)
        title = self._company_env(options)._report_title()
        if options['date_from']:
            return '%s %s - %s' % (title,
                                   fields.Date.to_string(options['date_from']),
                                   fields.Date.to_string(options['date_to']))
        return _("%(title)s as of %(date)s", title=title,
                 date=fields.Date.to_string(options['date_to']))

    @staticmethod
    def _json(options):
        """Options with dates as strings (JSON)."""
        return {key: fields.Date.to_string(value)
                if hasattr(value, 'isoformat') else value
                for key, value in options.items()}

    def _kit_amount_text(self, value, options, currency):
        """An amount as on the screen: amount unit (as is, without
        decimals, K, M) and currency symbol options (PDF)."""
        divisor, digits, suffix, _xlsx = AMOUNT_UNITS[options['amount_unit']]
        text = formatLang(self.env, value / divisor, digits=currency.decimal_places
                          if digits is None else digits) + suffix
        if options['currency_symbol'] and currency.symbol:
            parts = (text, '\N{NO-BREAK SPACE}', currency.symbol)
            text = ''.join(parts if currency.position == 'after' else parts[::-1])
        return text

    def _export_table(self, options):
        """The report as a table for the PDF and the XLSX: recomputed on the
        server from the options only."""
        data = self.get_report(options)
        options = data['options']
        # Under the title: the company, the period and the currency.
        meta = [
            [_("Company"), ', '.join(data['branches'])],
            [_("Period"), '%s - %s' % (
                fields.Date.to_string(options['date_from']),
                fields.Date.to_string(options['date_to']))]
            if options['date_from'] else
            [_("As of"), fields.Date.to_string(options['date_to'])],
            [_("Currency"), self.env['res.company'].browse(
                options['company_id']).currency_id.name],
        ]
        columns = [{'label': '', 'width': 50}] + [
            {'label': col['name'], 'width': 16,
             'num': col.get('type') == 'monetary'}
            for col in data['columns']]
        rows = [{'cells': [line['name']] + list(line['columns']),
                 'bold': line['style'] in ('1', '2', '3')
                 if line.get('style') else
                 line.get('class') in ('total', 'main', 'section') or (
                     line.get('level', 0) == 0 and line.get('unfolded')),
                 'highlight': line.get('class') in ('total', 'main'),
                 'style': line.get('style'),
                 'indent': line.get('level', 0),
                 # PDF statement lines: main section, subtotal, final total
                 'kind': self._kit_row_kind(line)}
                for line in data['lines']]
        currency = self.env['res.company'].browse(options['company_id']).currency_id
        return data, {'title': data['title'], 'meta': meta,
                      'columns': columns, 'rows': rows,
                      'num_format': self._kit_xlsx_number_format(options, currency)}

    @staticmethod
    def _kit_xlsx_number_format(options, currency):
        """Excel number format of the amounts, as on the screen: the amount
        unit, the decimals of the currency (as is), the currency symbol in
        its position when the option is on; negatives in red. Cells keep
        the exact amounts."""
        number = AMOUNT_UNITS[options['amount_unit']][3]
        if options['amount_unit'] == 'full':
            digits = currency.decimal_places
            number = '#,##0' + ('.' + '0' * digits if digits else '')
        positive, negative = number, '-' + number
        if options['currency_symbol'] and currency.symbol:
            symbol = currency.symbol.replace('"', '\\"')
            if currency.position == 'after':
                literal = '"\N{NO-BREAK SPACE}%s"' % symbol
                positive, negative = positive + literal, negative + literal
            else:
                literal = '"%s\N{NO-BREAK SPACE}"' % symbol
                positive, negative = literal + positive, literal + negative
        return '%s;[Red]%s' % (positive, negative)

    @staticmethod
    def _kit_row_kind(line):
        """Role of a line in the PDF: ``main`` section (grey band),
        ``subtotal`` ("Total ..." line, rule over the amounts), ``grand``
        final total (rule over, double rule under) or ``''``."""
        if line.get('class') == 'total':
            return 'grand'
        if line.get('class') == 'main':
            return 'main'
        if str(line.get('id') or '').startswith('total_'):
            return 'subtotal'
        return ''

    # ------------------------------------------------------------------
    # Saved filters (core ``ir.filters``: one per user, report and menu)
    # ------------------------------------------------------------------
    def _filter_action(self, action_id):
        """Id of the menu action of this report, or False. Users cannot read
        client actions: sudo only to check its tag and report model."""
        action = self.env['ir.actions.client'].sudo().browse(
            action_id if isinstance(action_id, int) else []).exists()
        return action.id if action.tag == 'kit_dynamic_report' and (
            action.params or {}).get('model') == self._name else False

    def _filter_domain(self, action_id):
        return [('model_id', '=', self._name),
                ('action_id', '=', self._filter_action(action_id)),
                ('user_ids', 'in', [self.env.uid])]

    @api.model
    def get_saved_filters(self, action_id=None):
        """Filters saved by the user on this report and menu, with their
        options (applied through ``get_report``, so checked again)."""
        res = []
        for saved in self.env['ir.filters'].search(
                self._filter_domain(action_id)):
            try:
                options = ast.literal_eval(saved.context)
            except (ValueError, SyntaxError):
                continue
            res.append({'id': saved.id, 'name': saved.name,
                        'is_default': saved.is_default,
                        'options': options if isinstance(options, dict)
                        else {}})
        return res

    @api.model
    def action_save_filter(self, options, name, action_id=None,
                           is_default=False):
        """Save the current options under ``name`` for the current user."""
        name = (name or '').strip()
        if not name:
            raise UserError(_("Give the filter a name."))
        options = self._json(self._normalize_options(options))
        for key in ('company_id', 'unfolded'):
            options.pop(key)
        if options['date_preset'] != 'custom':
            options.pop('date_from')
            options.pop('date_to')
        filters = self.env['ir.filters']
        if is_default:
            filters.search(self._filter_domain(action_id)).filtered(
                'is_default').is_default = False
        filters.create({
            'name': name[:100],
            'model_id': self._name,
            'action_id': self._filter_action(action_id),
            'user_ids': [self.env.uid],
            'context': repr(options),
            'is_default': bool(is_default),
        })
        return self.get_saved_filters(action_id)

    def _kit_export_heading(self, result):
        """Heading texts shared by the PDF and the XLSX: the company and its
        address on one line, under the title the period in words with the
        currency of the amounts, then (when set) draft entries included and
        the selected branches, and the print date."""
        company = self.env['res.company'].browse(result['options']['company_id'])
        address = company.partner_id._display_address(without_name=True)
        heading_line = result['heading']['period']
        if not result['options']['currency_symbol']:
            heading_line = _("%(period)s · Amounts in %(currency)s",
                             period=heading_line, currency=company.currency_id.name)
        filters = []
        if 'target_move' in self._filters \
                and result['options'].get('target_move') == 'all':
            filters.append(_("Including draft entries"))
        # the page header names the company: only the other branches here
        branches = [name for name in result['branches'] if name != company.name]
        if branches:
            filters.append(_("Branches: %s", ', '.join(branches)))
        return {
            'company': company,
            'company_address': ', '.join(
                part.strip() for part in address.splitlines() if part.strip()),
            'heading_line': heading_line,
            'filters_line': ' · '.join(filters),
            'print_stamp': format_datetime(self.env, fields.Datetime.now(),
                                           dt_format='d MMM yyyy, HH:mm'),
        }

    def get_xlsx_report(self, options, response):
        """Called by the /xlsx_report controller with the report options."""
        result, table = self._export_table(options)
        heading = self._kit_export_heading(result)
        company = heading['company']
        table.update({
            'company_name': company.name,
            'company_address': heading['company_address'],
            # Odoo 20 binary fields hold a BinaryValue: its raw bytes
            'kit_logo': company.logo.content if company.logo else False,
            'heading_line': heading['heading_line'],
            'filters_line': heading['filters_line'],
            'print_stamp': heading['print_stamp'],
            'currency_digits': company.currency_id.decimal_places,
        })
        write_xlsx_table(self.env, table, response)

    def get_csv_report(self, options, response):
        """CSV for other tools: a header row, then one row per line (the
        level as leading spaces), amounts exact with a dot and no thousands
        separator whatever the amount unit; UTF-8 with BOM (Excel)."""
        data, table = self._export_table(options)
        digits = self.env['res.company'].browse(
            data['options']['company_id']).currency_id.decimal_places
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([col['label'] for col in table['columns']])
        for row in table['rows']:
            cells = []
            for index, value in enumerate(row['cells']):
                if isinstance(value, float | int) and not isinstance(value, bool):
                    # rounded first, so float leftovers and -0.0 give 0.00
                    value = '%.*f' % (digits, round(value, digits) or 0.0)
                elif index == 0:
                    value = '  ' * (row.get('indent') or 0) + str(value or '')
                cells.append(value)
            writer.writerow(cells)
        response.stream.write(('\ufeff' + output.getvalue()).encode('utf-8'))


class ReportDynamicPdf(models.AbstractModel):
    """PDF of any dynamic report, recomputed from its options."""
    _name = 'report.base_accounting_kit.dynamic_report_pdf'
    _description = 'Dynamic Report PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        model = data.get('model')
        if model not in self.env or not getattr(
                self.env[model], '_dynamic_report', False):
            raise UserError(_("This report cannot be printed."))
        report = self.env[model]
        result, table = report._export_table(data.get('options') or {})
        heading = report._kit_export_heading(result)
        company = heading['company']
        return {
            'doc_ids': [],
            'doc_model': model,
            'report': result,
            'table': table,
            'heading_line': heading['heading_line'],
            'filters_line': heading['filters_line'],
            'kit_print_stamp': heading['print_stamp'],
            'company': company,
            # one line for the page header
            'company_address': heading['company_address'],
            'report_currency': company.currency_id,
            'currency_symbol': result['options']['currency_symbol'],
            'format_amount': lambda value: report._kit_amount_text(
                value, result['options'], company.currency_id),
        }
