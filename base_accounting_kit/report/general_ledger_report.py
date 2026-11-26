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
from datetime import timedelta

from odoo import api, fields, models, _

from ..models.report_company import get_report_company


class ReportGeneralLedger(models.AbstractModel):
    _name = 'report.base_accounting_kit.report_general_ledger'
    _description = 'General Ledger Report'

    def _sum_by_account(self, account_ids, ctx):
        """Return ``{account_id: {'debit', 'credit', 'balance'}}`` for the
        move lines matching ``_query_get`` with the given context."""
        if not account_ids:
            return {}
        tables, where_clause, where_params = self.env[
            'account.move.line'].with_context(**ctx)._query_get()
        tables = tables.replace('"', '') if tables else 'account_move_line'
        where = (' AND ' + where_clause) if where_clause.strip() else ''
        self.env.cr.execute(
            "SELECT account_id, COALESCE(SUM(debit), 0) AS debit, "
            "COALESCE(SUM(credit), 0) AS credit, "
            "COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0) AS balance "
            "FROM " + tables + " WHERE account_id IN %s" + where +
            " GROUP BY account_id",
            (tuple(account_ids),) + tuple(where_params))
        return {row.pop('account_id'): row
                for row in self.env.cr.dictfetchall()}

    def _get_initial_balances(self, accounts):
        """Opening balances at the context ``date_from``.

        - Accounts with ``include_initial_balance`` (balance sheet): every
          line before ``date_from``.
        - Other accounts (income, expense, current year earnings): only the
          lines from the start of the fiscal year of ``date_from``.
        - Their lines from earlier fiscal years are returned apart as the
          "Result Brought Forward", so the opening balances still add up.

        :return: ``(initial, result_brought_forward)`` where ``initial`` is
            ``{account_id: {'debit', 'credit', 'balance'}}`` and
            ``result_brought_forward`` is a dict with the same keys plus
            ``account_id`` (the company's current year earnings account, or
            ``False`` if it has none), or ``None`` if there is nothing.
        """
        ctx = dict(self.env.context)
        date_from = ctx.get('date_from')
        if not date_from or not accounts:
            return {}, None
        date_from = fields.Date.to_date(date_from)
        company = get_report_company(self.env)
        fy_start = company.compute_fiscalyear_dates(date_from)['date_from']
        bs_accounts = accounts.filtered('include_initial_balance')
        pl_accounts = accounts - bs_accounts

        # Lines before date_from
        before = dict(ctx, date_from=date_from, date_to=False,
                      initial_bal=True, strict_range=True)
        initial = self._sum_by_account(bs_accounts.ids, before)
        # Current fiscal year part of the profit and loss accounts
        if fy_start < date_from:
            initial.update(self._sum_by_account(pl_accounts.ids, dict(
                ctx, date_from=fy_start,
                date_to=date_from - timedelta(days=1),
                initial_bal=False, strict_range=True)))
        # Earlier fiscal years: result brought forward
        earlier = self._sum_by_account(pl_accounts.ids, dict(
            ctx, date_from=fy_start, date_to=False, initial_bal=True,
            strict_range=True))
        rbf = None
        if earlier:
            rbf = {key: sum(vals[key] for vals in earlier.values())
                   for key in ('debit', 'credit', 'balance')}
            rbf['account_id'] = self.env['account.account'].search([
                *self.env['account.account']._check_company_domain(company),
                ('account_type', '=', 'equity_unaffected'),
            ], limit=1).id
        return initial, rbf

    @api.model
    def _initial_move_line(self, label, values):
        """A pseudo move line holding an opening amount."""
        return {
            'lid': 0, 'ldate': '', 'lcode': '', 'amount_currency': 0.0,
            'lref': '', 'lname': label, 'debit': values['debit'],
            'credit': values['credit'], 'balance': values['balance'],
            'lpartner_id': '', 'move_name': '', 'mmove_id': '',
            'currency_code': '', 'currency_id': None, 'invoice_id': '',
            'invoice_type': '', 'invoice_number': '', 'partner_name': '',
        }

    def _get_account_move_entry(self, accounts, init_balance, sortby,
                                display_account):
        """
        :param:
                accounts: the recordset of accounts
                init_balance: boolean value of initial_balance
                sortby: sorting by date or partner and journal
                display_account: type of account(receivable, payable and both)

        Returns a dictionary of accounts with following key and value {
                'code': account code,
                'name': account name,
                'debit': sum of total debit amount,
                'credit': sum of total credit amount,
                'balance': total balance,
                'amount_currency': sum of amount_currency,
                'move_lines': list of move line
        }
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}

        # Opening lines: initial balance (balance sheet accounts from the
        # beginning, profit and loss accounts from the fiscal year start)
        # and the result brought forward of earlier fiscal years.
        rbf = None
        if init_balance:
            initial, rbf = self._get_initial_balances(accounts)
            for account_id, values in initial.items():
                move_lines[account_id].append(
                    self._initial_move_line(_('Initial Balance'), values))
            if rbf and rbf['account_id'] in move_lines:
                move_lines[rbf['account_id']].append(
                    self._initial_move_line(_('Result Brought Forward'), rbf))

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace(
            'account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.id AS lid, l.account_id AS account_id, 
        l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, 
        l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, 
        COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - 
        COALESCE(SUM(l.credit), 0) AS balance,\
            m.name AS move_name, c.symbol AS currency_code, p.name AS 
            partner_name\
            FROM account_move_line l\
            JOIN account_move m ON (l.move_id=m.id)\
            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
            JOIN account_journal j ON (l.journal_id=j.id)\
            JOIN account_account acc ON (l.account_id = acc.id) \
            WHERE l.account_id IN %s ''' + filters + ''' GROUP BY l.id, 
            l.account_id, l.date, j.code, l.currency_id, l.amount_currency, 
            l.ref, l.name, m.name, c.symbol, p.name ORDER BY ''' + sql_sort)
        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        account_company = get_report_company(self.env)
        for account in accounts:
            currency = account.currency_id and account.currency_id or account_company.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(
                    res['balance']):
                account_res.append(res)

        if rbf and rbf['account_id'] not in move_lines:
            # No current year earnings account among the reported accounts:
            # show the result brought forward on its own.
            line = self._initial_move_line(_('Result Brought Forward'), rbf)
            account_res.append({
                'code': '', 'name': _('Result Brought Forward'),
                'debit': rbf['debit'], 'credit': rbf['credit'],
                'balance': rbf['balance'], 'move_lines': [line],
            })
        return account_res
