# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import timedelta

from odoo import api, fields, models
from odoo.fields import Domain
from odoo.tools.misc import format_amount, format_date, formatLang

from .ai_chat_assistant import DEFAULT_MAX_ROWS, DEPTH_QUESTION, PERIODS, _keywords, _score

# account types by the group of the balance they belong to, and the sign that shows
# their amounts as accountants read them: income, liabilities and equity are credits
FIGURE_SIGNS = {'income': -1, 'expense': 1, 'asset': 1, 'liability': -1, 'equity': -1}
# income and expenses are amounts of a period; assets, liabilities and equity are
# balances at the end of it
PERIOD_GROUPS = ('income', 'expense')
FIGURE_PERIODS = {
    'default': ("No period named", None, None),
    'fiscal_year': ("This fiscal year", None, None),
    'last_fiscal_year': ("Last fiscal year, previous fiscal year", None, None),
    **{key: value for key, value in PERIODS.items() if key not in ('none', 'past', 'future')},
    'all_time': ("Since the beginning, all time, lifetime", None, None),
}
FIGURE_BREAKDOWNS = {
    'none': ("One figure", None),
    'month': ("Per month", 'date:month'),
    'quarter': ("Per quarter", 'date:quarter'),
    'year': ("Per year", 'date:year'),
    'account': ("Per account", 'account_id'),
    'partner': ("Per partner, customer or vendor", 'partner_id'),
    'journal': ("Per journal", 'journal_id'),
}


class AiChatAssistant(models.AbstractModel):
    """ Accounting figures (profit, income, expenses, assets, cash...) of a period,
    computed from the posted journal items, as accounting reports do.

    The figures are not hard coded: they are built from Odoo's classification of the
    accounts (the account types and the groups they belong to), which every chart of
    accounts uses, plus the standard net and gross profit. The decision model chooses
    the figure, the period and the breakdown; the amounts are computed by the ORM as
    the current user, so accounting access rights and company rules apply.
    """
    _inherit = 'ai.chat.assistant'

    # ------------------------------------------------------------
    # Catalog
    # ------------------------------------------------------------

    @api.model
    def _can_compute_figures(self):
        return 'account.move.line' in self.env and self.env['account.move.line'].has_access('read') \
            and self.env['account.account'].has_access('read')

    @api.model
    def _get_figure_catalog(self):
        """ The figures that can be computed, by key: ``{key: {'label', 'description',
        'types', 'sign', 'scope', 'components'}}``. """
        Account = self.env['account.account']
        selection = Account._fields['account_type']._description_selection(self.env)
        types_by_group = {}
        catalog = {}
        for account_type, label in selection:
            group = account_type.split('_')[0]
            if group not in FIGURE_SIGNS:
                continue
            types_by_group.setdefault(group, []).append(account_type)
            catalog[f"type:{account_type}"] = {
                'label': label,
                'description': self.env._("%(label)s accounts", label=label),
                'types': [account_type],
                'group': group,
            }
        group_labels = {
            'income': self.env._("Total Income"),
            'expense': self.env._("Total Expenses"),
            'asset': self.env._("Total Assets"),
            'liability': self.env._("Total Liabilities"),
            'equity': self.env._("Total Equity"),
        }
        for group, label in group_labels.items():
            if group not in types_by_group:
                continue
            types = types_by_group[group]
            if group == 'equity':
                # the earnings not yet closed into equity belong to it
                types = types + types_by_group.get('income', []) + types_by_group.get('expense', [])
            catalog[f"group:{group}"] = {'label': label, 'description': label, 'types': types, 'group': group}
        if 'income' in types_by_group and 'expense' in types_by_group:
            catalog['net_profit'] = {
                'label': self.env._("Net Profit"),
                'description': self.env._("Net profit or loss: income minus expenses (profit, result, earnings)"),
                'types': types_by_group['income'] + types_by_group['expense'],
                'group': 'income',
                'components': ['group:income', 'group:expense'],
            }
            if 'expense_direct_cost' in types_by_group['expense']:
                catalog['gross_profit'] = {
                    'label': self.env._("Gross Profit"),
                    'description': self.env._("Gross profit: income minus cost of revenue"),
                    'types': types_by_group['income'] + ['expense_direct_cost'],
                    'group': 'income',
                    'components': ['group:income', 'type:expense_direct_cost'],
                }
        for figure in catalog.values():
            figure['sign'] = FIGURE_SIGNS[figure['group']]
            figure['scope'] = 'period' if figure['group'] in PERIOD_GROUPS else 'balance'
        return catalog

    @api.model
    def _get_figure_candidate(self, keywords):
        """ The accounting figures, as an answer offered to the decision model, when
        the question names one of them, or asks for accounting figures as the agent
        read it (profit, turnover, earnings...). """
        asked = self._get_intent().get('figures')
        if not (keywords or asked) or not self._can_compute_figures():
            return None
        catalog = self._get_figure_catalog()
        words = {}
        for figure in catalog.values():
            self._add_words(words, figure['label'], 3)
        score = max(_score(keywords, tuple(words.items())), 3 if asked else 0)
        if not score:
            return None
        matching = [
            figure['label'] for figure in catalog.values()
            if _score(keywords, [(word, 1) for word in _keywords(figure['label'])])
        ]
        return {
            'model': 'account.move.line',
            'label': self.env['account.move.line']._description,
            'score': score,
            'path': '',
            'domain': '',
            'figures': True,
            'examples': (matching or [catalog[key]['label'] for key in ('net_profit', 'group:income')
                                      if key in catalog])[:4],
        }

    # ------------------------------------------------------------
    # Decisions
    # ------------------------------------------------------------

    @api.model
    def _get_figure_plan(self, question, usage):
        """ The figure, period and breakdown the question asks for. """
        catalog = self._get_figure_catalog()
        breakdowns = dict(FIGURE_BREAKDOWNS)
        if len(self.env.companies) > 1:
            breakdowns['company'] = ("Per company", 'company_id')
        questions = {
            'figure': {
                'type': 'choice',
                'instructions': "Which accounting figure does the question ask for?",
                'criteria': {key: figure['description'] for key, figure in catalog.items()},
            },
            'period': {
                'type': 'choice',
                'instructions': "For which period?",
                'criteria': {key: description for key, (description, _start, _end) in FIGURE_PERIODS.items()},
            },
            'breakdown': {
                'type': 'choice',
                'instructions': "Is the figure broken down? 'none' for one figure.",
                'criteria': {key: description for key, (description, _spec) in breakdowns.items()},
            },
            'depth': DEPTH_QUESTION,
        }
        answers = self._decide(
            f"Accounting question, answered from the posted journal items: {question}", questions, usage,
        )
        plan = {
            'kind': 'figure',
            'model': 'account.move.line',
            'question': question,
            'figure': self._get_choice(answers, 'figure', catalog, 'net_profit'),
            'period': self._get_choice(answers, 'period', FIGURE_PERIODS, 'default'),
            'breakdown': self._get_choice(answers, 'breakdown', breakdowns, 'none'),
            'limit': self._extract_limit(question),
        }
        plan['depth'], plan['depth_confidence'] = self._read_depth(answers)
        if plan['figure'] not in catalog:
            plan['figure'] = next(iter(catalog))
        return plan

    # ------------------------------------------------------------
    # Computation
    # ------------------------------------------------------------

    @api.model
    def _get_figure_dates(self, figure, period):
        """ First and last day of a figure: balances have no first day. """
        today = fields.Date.context_today(self)
        company = self.env.company
        if period in ('default', 'fiscal_year'):
            start = company.compute_fiscalyear_dates(today)['date_from']
            end = today if period == 'default' else company.compute_fiscalyear_dates(today)['date_to']
        elif period == 'last_fiscal_year':
            previous_year = company.compute_fiscalyear_dates(today)['date_from'] - timedelta(days=1)
            dates = company.compute_fiscalyear_dates(previous_year)
            start, end = dates['date_from'], dates['date_to']
        elif period == 'all_time':
            start, end = None, today
        else:
            _description, start, end = PERIODS[period]
            start = start and self._resolve_value(start)
            end = end and self._resolve_value(end)
        if figure['scope'] == 'balance':
            start = None
        return start, end or today

    @api.model
    def _figure_domain(self, figure, start, end):
        domain = Domain([
            ('parent_state', '=', 'posted'),
            ('account_id.account_type', 'in', figure['types']),
            ('company_id', 'in', self.env.companies.ids),
            ('date', '<=', end),
        ])
        if start:
            domain &= Domain('date', '>=', start)
        return domain

    @api.model
    def _run_figure(self, plan):
        """ Compute a figure of the plan as the current user.

        :return: the result to display, and a one line summary of it
        """
        Line = self.env['account.move.line']
        Line.check_access('read')
        catalog = self._get_figure_catalog()
        figure = catalog[plan['figure']]
        start, end = self._get_figure_dates(figure, plan['period'])
        if start:
            period_label = self.env._(
                "%(start)s to %(end)s", start=format_date(self.env, start), end=format_date(self.env, end),
            )
        else:
            period_label = self.env._("Balance at %s", format_date(self.env, end))
        currencies = self.env.companies.currency_id
        breakdowns = dict(FIGURE_BREAKDOWNS, company=("Per company", 'company_id'))
        breakdown = plan.get('breakdown') or 'none'
        # amounts of companies in other currencies are not added up
        if breakdown == 'none' and len(currencies) > 1:
            breakdown = 'company'
        domain = self._figure_domain(figure, start, end)
        base = {
            'title': f"{figure['label']} · {period_label}",
            'heading': figure['label'],
            'tags': [period_label],
            'model': 'account.move.line',
            'domain': self._serialize_domain(domain),
        }
        currency = self.env.company.currency_id

        def amount(value, row_currency=None):
            return format_amount(self.env, value, row_currency or currency)

        if breakdown == 'none':
            keys = [plan['figure'], *figure.get('components', [])]
            items = []
            for key in keys:
                item = catalog[key]
                [(balance,)] = Line._read_group(self._figure_domain(item, start, end), [], ['balance:sum'])
                items.append((item['label'], (balance or 0.0) * item['sign']))
            columns = [{'label': label, 'numeric': True, 'kind': False} for label, _value in items]
            row = {'id': False, 'cells': [amount(value) for _label, value in items],
                   'raw': [value for _label, value in items]}
            result = {
                **base, 'type': 'value', 'label': figure['label'], 'value': row['cells'][0],
                'columns': columns, 'rows': [row],
            }
            return result, f"{figure['label']} ({period_label}): {row['cells'][0]}"

        _description, group_spec = breakdowns[breakdown]
        is_period = ':' in group_spec
        max_rows = int(self.env['ir.config_parameter'].sudo().get_param('ai_chat_pro.max_rows') or 0) or DEFAULT_MAX_ROWS
        limit = min(plan.get('limit') or max_rows, max_rows)
        # the biggest amounts first, as they read: credits are negative balances
        order = f"{group_spec} asc" if is_period else f"balance:sum {'desc' if figure['sign'] > 0 else 'asc'}"
        groups = Line._read_group(domain, [group_spec], ['balance:sum'], order=order, limit=limit)
        group_field = Line._fields[group_spec.partition(':')[0]]
        row_model = group_field.comodel_name if group_field.type == 'many2one' else False
        if row_model and not self.env[row_model].has_access('read'):
            row_model = False
        rows = []
        for group_value, balance in groups:
            value = (balance or 0.0) * figure['sign']
            row_currency = group_value.currency_id if group_spec == 'company_id' and group_value else None
            rows.append({
                'id': group_value.id if row_model and group_value else False,
                'cells': [self._format_group_value(Line, group_spec, group_value), amount(value, row_currency)],
                'raw': [None, value],
            })
        result = {
            **base,
            'type': 'table',
            'openable': bool(row_model),
            'row_model': row_model,
            'total': len(rows),
            'columns': [
                {'label': group_field._description_string(self.env), 'numeric': False,
                 'kind': 'date' if is_period else False},
                {'label': figure['label'], 'numeric': True, 'kind': False},
            ],
            'rows': rows,
        }
        if not rows:
            return result, self.env._("No posted journal item for %(figure)s (%(period)s).",
                                      figure=figure['label'], period=period_label)
        [(balance,)] = Line._read_group(domain, [], ['balance:sum'])
        total = (balance or 0.0) * figure['sign']
        summary = amount(total) if len(currencies) == 1 else formatLang(self.env, total)
        return result, f"{figure['label']} ({period_label}): {summary}"
