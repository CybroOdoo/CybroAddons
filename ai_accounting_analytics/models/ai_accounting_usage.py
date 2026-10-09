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
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import date_utils
from odoo.tools.misc import format_date

DASHBOARD_PERIODS = ('this_month', 'last_month', 'last_30_days', 'this_year', 'all_time')
RECENT_ANSWERS = 8


class AiAccountingUsage(models.Model):
    """Immutable log of every call made to an AI provider: tokens and cost."""
    _name = 'ai.accounting.usage'
    _description = 'AI Usage'
    _order = 'id desc'
    _rec_name = 'model_id'

    user_id = fields.Many2one('res.users', string='User', required=True, readonly=True,
                              default=lambda self: self.env.user, index=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    chat_id = fields.Many2one('ai.accounting.chat', string='Conversation', ondelete='set null')
    message_id = fields.Many2one('ai.accounting.message', string='Message', ondelete='set null')
    model_id = fields.Many2one('ai.accounting.model', string='Model', ondelete='set null', index=True)
    provider_id = fields.Many2one(related='model_id.provider_id', store=True, string='Provider')
    step = fields.Integer(help="Position of the call in the answer (1 = first call).")
    input_tokens = fields.Integer(help="Uncached input tokens.")
    cached_tokens = fields.Integer(help="Input tokens read from the prompt cache.")
    cache_write_tokens = fields.Integer(help="Input tokens written to the prompt cache.")
    output_tokens = fields.Integer(help="Output tokens, reasoning included.")
    total_tokens = fields.Integer(compute='_compute_total_tokens', store=True)
    cost = fields.Float(string='Cost (USD)', digits=(16, 6))
    duration_ms = fields.Integer(string='Duration (ms)')

    @api.depends('input_tokens', 'cached_tokens', 'cache_write_tokens', 'output_tokens')
    def _compute_total_tokens(self):
        for usage in self:
            usage.total_tokens = usage.input_tokens + usage.cached_tokens \
                + usage.cache_write_tokens + usage.output_tokens

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    @api.model
    def ai_get_dashboard(self, period='this_month'):
        """Figures of the AI Usage & Cost dashboard for ``period``, read with
        the user's own access rights (a Chief Accountant sees their own usage,
        an administrator everyone's). Costs are in USD."""
        if period not in DASHBOARD_PERIODS:
            raise UserError(self.env._("Unknown period %s.", period))
        (start, end), (previous_start, previous_end) = self._ai_dashboard_ranges(period)
        domain = [('create_date', '<', end)] + ([('create_date', '>=', start)] if start else [])
        figures = self._ai_dashboard_figures(domain)
        previous = self._ai_dashboard_figures(
            [('create_date', '>=', previous_start), ('create_date', '<', previous_end)]) \
            if previous_start else None

        def delta(key):
            if not previous or not previous[key]:
                return None
            return round((figures[key] - previous[key]) / previous[key] * 100, 1)

        return {
            'period': period,
            'has_data': bool(self.search_count([], limit=1)),
            'kpis': {key: {'value': figures[key], 'delta': delta(key)} for key in figures if key != '_mix'},
            'timeline': self._ai_dashboard_timeline(domain, start, end),
            'by_model': self._ai_dashboard_breakdown(domain, 'model_id'),
            'by_user': self._ai_dashboard_breakdown(domain, 'user_id'),
            'token_mix': [
                {'key': key, 'value': figures['_mix'][key]}
                for key in ('input_tokens', 'cached_tokens', 'cache_write_tokens', 'output_tokens')],
            'recent': self._ai_dashboard_recent(domain),
        }

    @api.model
    def _ai_dashboard_ranges(self, period):
        """``((start, end), (previous_start, previous_end))`` as naive UTC
        datetimes; periods start at local midnight. The previous range has
        the same length (month-to-date is compared with the same days of the
        month before)."""
        zone = ZoneInfo(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        now = fields.Datetime.now()
        today = now.replace(tzinfo=ZoneInfo('UTC')).astimezone(zone).date()

        def utc(day):
            return datetime.combine(day, time.min, tzinfo=zone).astimezone(ZoneInfo('UTC')).replace(tzinfo=None)

        month_start = date_utils.start_of(today, 'month')
        if period == 'this_month':
            start, end = utc(month_start), now
            return (start, end), (start - relativedelta(months=1), end - relativedelta(months=1))
        if period == 'last_month':
            start, end = utc(month_start - relativedelta(months=1)), utc(month_start)
            return (start, end), (utc(month_start - relativedelta(months=2)), start)
        if period == 'last_30_days':
            start = utc(today - timedelta(days=29))
            return (start, now), (start - timedelta(days=30), start)
        if period == 'this_year':
            start = utc(date_utils.start_of(today, 'year'))
            return (start, now), (start - relativedelta(years=1), now - relativedelta(years=1))
        return (False, now), (False, False)

    @api.model
    def _ai_dashboard_figures(self, domain):
        (cost, tokens, input_tokens, cached, cache_write, output, calls, answers, duration), = self._read_group(
            domain, [], ['cost:sum', 'total_tokens:sum', 'input_tokens:sum', 'cached_tokens:sum',
                         'cache_write_tokens:sum', 'output_tokens:sum', '__count', 'message_id:count_distinct',
                         'duration_ms:sum'])
        # Saved by the prompt cache: cached tokens billed at the cached price
        # instead of the input price.
        savings = sum(
            (model.price_input - (model.price_cached or model.price_input)) * cached_tokens / 1_000_000
            for model, cached_tokens in self._read_group(domain, ['model_id'], ['cached_tokens:sum']) if model)
        prompt = (input_tokens or 0) + (cached or 0) + (cache_write or 0)
        answers = answers or 0
        return {
            'cost': cost or 0.0,
            'tokens': tokens or 0,
            'answers': answers,
            'calls': calls,
            'cost_per_answer': (cost or 0.0) / answers if answers else 0.0,
            'cache_savings': savings,
            'cache_rate': round((cached or 0) / prompt * 100, 1) if prompt else 0.0,
            'seconds_per_answer': round((duration or 0) / answers / 1000, 1) if answers else 0.0,
            '_mix': {'input_tokens': input_tokens or 0, 'cached_tokens': cached or 0,
                     'cache_write_tokens': cache_write or 0, 'output_tokens': output or 0},
        }

    @api.model
    def _ai_dashboard_timeline(self, domain, start, end):
        """Cost and tokens per day, or per month over long ranges; empty
        buckets included so the chart has no gaps."""
        if not start:
            first = self.search(domain, order='create_date asc', limit=1).create_date
            start = first or end
        granularity = 'day' if (end - start).days <= 62 else 'month'
        rows = {day: (cost, tokens) for day, cost, tokens in self._read_group(
            domain, ['create_date:%s' % granularity], ['cost:sum', 'total_tokens:sum'])}
        zone = ZoneInfo(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        bucket = date_utils.start_of(start.replace(tzinfo=ZoneInfo('UTC')).astimezone(zone).replace(tzinfo=None),
                                     granularity)
        last = end.replace(tzinfo=ZoneInfo('UTC')).astimezone(zone).replace(tzinfo=None)
        step = relativedelta(days=1) if granularity == 'day' else relativedelta(months=1)
        labels, costs, tokens = [], [], []
        while bucket <= last and len(labels) < 400:
            cost, count = rows.get(bucket, (0.0, 0))
            labels.append(format_date(self.env, bucket, date_format='d MMM' if granularity == 'day' else 'MMM yyyy'))
            costs.append(round(cost or 0.0, 6))
            tokens.append(count or 0)
            bucket += step
        return {'granularity': granularity, 'labels': labels, 'cost': costs, 'tokens': tokens}

    @api.model
    def _ai_dashboard_breakdown(self, domain, field_name):
        groups = self._read_group(domain, [field_name], ['cost:sum', 'total_tokens:sum', 'message_id:count_distinct'],
                                  order='cost:sum desc')
        total = sum(cost or 0.0 for _record, cost, _tokens, _answers in groups)
        rows = []
        for record, cost, tokens, answers in groups:
            # Models are listed with their provider on a line of its own.
            name = record.name if field_name == 'model_id' else record.display_name
            row = {'id': record.id, 'name': name or self.env._("Unknown"), 'cost': cost or 0.0,
                   'tokens': tokens or 0, 'answers': answers or 0,
                   'share': round((cost or 0.0) / total * 100, 1) if total else 0.0}
            if field_name == 'model_id':
                row['provider'] = record.provider_id.name or ''
            rows.append(row)
        return rows

    @api.model
    def _ai_dashboard_recent(self, domain):
        """The current user's latest answers, with the question asked."""
        groups = self._read_group(domain + [('user_id', '=', self.env.uid), ('message_id', '!=', False)],
                                  ['message_id'], ['cost:sum', 'total_tokens:sum', 'create_date:max'],
                                  order='create_date:max desc, message_id desc', limit=RECENT_ANSWERS)
        Message = self.env['ai.accounting.message']
        recent = []
        for message, cost, tokens, last in groups:
            question = Message.search([('chat_id', '=', message.chat_id.id), ('role', '=', 'user'),
                                       ('id', '<', message.id)], order='id desc', limit=1)
            recent.append({
                'chat_id': message.chat_id.id,
                'question': (question.content or message.chat_id.name or '')[:160],
                'model': message.model_id.name or '',
                'error': message.error,
                'steps': len(message.steps or []),
                'tokens': tokens or 0,
                'cost': cost or 0.0,
                'date': fields.Datetime.to_string(last),
            })
        return recent
