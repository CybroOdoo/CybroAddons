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
from odoo import models, _

from ..models.report_company import get_report_company


class ReportTrialBalance(models.AbstractModel):
    _name = 'report.base_accounting_kit.report_trial_balance'
    _description = 'Trial Balance Report'

    def _get_accounts(self, accounts, display_account):
        """ compute the balance, debit and credit for the provided accounts
            :Arguments:
                `accounts`: list of accounts record,
                `display_account`: it's used to display either all accounts or those accounts which balance is > 0
            :Returns a list of dictionary of Accounts with following key and value
                `name`: Account name,
                `code`: Account code,
                `credit`: total amount of credit,
                `debit`: total amount of debit,
                `balance`: total amount of balance,
        """

        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = self.env[
            'account.move.line']._query_get()
        tables = tables.replace('"', '')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        # compute the balance, debit and credit for the provided accounts
        request = (
                    "SELECT account_id AS id, SUM(debit) AS debit, "
                    "SUM(credit) AS credit, (SUM(debit) - SUM(credit)) "
                    "AS balance" +
                    " FROM " + tables + " WHERE account_id IN %s " +
                    filters + " GROUP BY account_id")
        params = (tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        # Opening balances at the start date (same rules as the general
        # ledger: profit and loss accounts restart at the fiscal year, the
        # earlier years' result is brought forward to current year earnings)
        initial, rbf = self.env[
            'report.base_accounting_kit.report_general_ledger'].with_context(
            self.env.context)._get_initial_balances(accounts)
        initial = {key: vals['balance'] for key, vals in initial.items()}
        if rbf and rbf['account_id'] in accounts.ids:
            initial[rbf['account_id']] = initial.get(
                rbf['account_id'], 0.0) + rbf['balance']

        account_res = []
        account_company = get_report_company(self.env)
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = (account.currency_id and account.currency_id or
                        account_company.currency_id)
            res['id'] = account.id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result:
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
            res['init_balance'] = initial.get(account.id, 0.0)
            res['end_balance'] = res['init_balance'] + res['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(
                    res['end_balance']):
                account_res.append(res)
            if display_account == 'movement' and (
                    not currency.is_zero(res['debit']) or not currency.is_zero(
                    res['credit'])):
                account_res.append(res)
        if rbf and rbf['account_id'] not in accounts.ids:
            # No current year earnings account: show it on its own row.
            account_res.append({
                'code': '', 'name': _('Result Brought Forward'),
                'debit': 0.0, 'credit': 0.0, 'balance': 0.0,
                'init_balance': rbf['balance'], 'end_balance': rbf['balance'],
            })
        return account_res
