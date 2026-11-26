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
from odoo import models

from ..models.report_company import get_report_company


class ReportPartnerLedger(models.AbstractModel):
    _name = 'report.base_accounting_kit.report_partnerledger'
    _description = 'Partner Ledger Report'

    def _base_filters(self, data, ctx):
        """Return ``(tables, where, params)`` for the partner move lines of
        the selected accounts, move states and reconciliation option."""
        tables, where_clause, where_params = self.env[
            'account.move.line'].with_context(**ctx)._query_get()
        reconcile_clause = "" if data['form']['reconciled'] else \
            ' AND "account_move_line".full_reconcile_id IS NULL '
        where = (' "account_move_line".partner_id IS NOT NULL'
                 ' AND m.state IN %s'
                 ' AND "account_move_line".account_id IN %s'
                 ' AND ' + where_clause + reconcile_clause)
        params = [tuple(data['computed']['move_state']),
                  tuple(data['computed']['account_ids']) or (0,)] + \
            list(where_params)
        return tables, where, params

    def _initial_balances(self, data):
        """Return ``{partner_id: {'debit', 'credit', 'balance'}}`` for the
        lines before the start date (empty without a start date)."""
        used_context = data['form'].get('used_context', {})
        if not used_context.get('date_from'):
            return {}
        ctx = dict(used_context, date_to=False, initial_bal=True,
                   strict_range=True)
        tables, where, params = self._base_filters(data, ctx)
        self.env.cr.execute(
            'SELECT "account_move_line".partner_id,'
            ' COALESCE(SUM("account_move_line".debit), 0) AS debit,'
            ' COALESCE(SUM("account_move_line".credit), 0) AS credit'
            ' FROM ' + tables +
            ' JOIN account_move m ON (m.id = "account_move_line".move_id)'
            ' WHERE' + where +
            ' GROUP BY "account_move_line".partner_id', tuple(params))
        res = {}
        for row in self.env.cr.dictfetchall():
            res[row['partner_id']] = {
                'debit': row['debit'], 'credit': row['credit'],
                'balance': row['debit'] - row['credit']}
        return res

    def _period_lines(self, data):
        """Return ``{partner_id: [line, ...]}`` for the report period, in
        one query for all partners."""
        tables, where, params = self._base_filters(
            data, data['form'].get('used_context', {}))
        self.env.cr.execute(
            'SELECT "account_move_line".id, "account_move_line".partner_id,'
            ' "account_move_line".date, j.code,'
            ' COALESCE(acc.name->>%s, acc.name->>\'en_US\') AS a_name,'
            ' "account_move_line".ref, m.name AS move_name,'
            ' "account_move_line".name, "account_move_line".debit,'
            ' "account_move_line".credit,'
            ' "account_move_line".amount_currency,'
            ' "account_move_line".currency_id, c.symbol AS currency_code'
            ' FROM ' + tables +
            ' JOIN account_move m ON (m.id = "account_move_line".move_id)'
            ' LEFT JOIN account_journal j'
            ' ON ("account_move_line".journal_id = j.id)'
            ' LEFT JOIN account_account acc'
            ' ON ("account_move_line".account_id = acc.id)'
            ' LEFT JOIN res_currency c'
            ' ON ("account_move_line".currency_id = c.id)'
            ' WHERE' + where +
            ' ORDER BY "account_move_line".partner_id,'
            ' "account_move_line".date, "account_move_line".id',
            (self.env.lang or 'en_US',) + tuple(params))
        currency = self.env['res.currency']
        res = {}
        for r in self.env.cr.dictfetchall():
            r['displayed_name'] = '-'.join(
                r[field_name] for field_name in ('move_name', 'ref', 'name')
                if r[field_name] not in (None, '', '/')
            )
            r['currency_id'] = currency.browse(r.get('currency_id'))
            res.setdefault(r['partner_id'], []).append(r)
        return res

    def _partner_data(self, data):
        """Compute, per partner, the opening balance, the period lines with
        a running balance and the totals; plus the grand total.

        :return: ``(partners, partner_data, grand_total)``
        """
        initial = self._initial_balances(data)
        lines = self._period_lines(data)
        currency = get_report_company(self.env, data['form']).currency_id
        partner_ids = set(lines)
        partner_ids.update(pid for pid, vals in initial.items()
                           if not currency.is_zero(vals['balance']))
        partners = self.env['res.partner'].browse(list(partner_ids))
        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))
        partner_data = {}
        grand_total = {'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
        for partner in partners:
            init = initial.get(partner.id)
            progress = init['balance'] if init else 0.0
            debit = init['debit'] if init else 0.0
            credit = init['credit'] if init else 0.0
            partner_lines = lines.get(partner.id, [])
            for line in partner_lines:
                progress += line['debit'] - line['credit']
                line['progress'] = progress
                debit += line['debit']
                credit += line['credit']
            partner_data[partner.id] = {
                'initial': init,
                'lines': partner_lines,
                'debit': debit,
                'credit': credit,
                'balance': debit - credit,
            }
            grand_total['debit'] += debit
            grand_total['credit'] += credit
        grand_total['balance'] = grand_total['debit'] - grand_total['credit']
        return partners, partner_data, grand_total
