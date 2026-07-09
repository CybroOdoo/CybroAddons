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
from odoo import fields, models


class AccountBalanceReport(models.TransientModel):
    _name = 'account.balance.report'
    _inherit = "account.common.account.report"
    _description = 'Trial Balance Report'

    name = fields.Char(string="Trial Balance", default="Trial Balance", required=True, translate=True)
    journal_ids = fields.Many2many('account.journal',
                                   'account_balance_report_journal_rel',
                                   'account_id', 'journal_id',
                                   string='Journals', required=True,
                                   default=[])
    enable_filter = fields.Boolean(
        string='Enable Comparison',
        help="Add a balance column for a second (comparison) period, plus a "
             "variance column.")
    date_from_cmp = fields.Date(string='Comparison Start Date')
    date_to_cmp = fields.Date(string='Comparison End Date')

    def _trial_balance_comparison(self, accounts):
        """Return ``{account_code: balance}`` for the comparison period."""
        if not self.enable_filter:
            return {}
        by_id = self._period_account_balances(
            accounts, self.date_from_cmp, self.date_to_cmp)
        return {a.code: by_id[a.id] for a in accounts if a.id in by_id}

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form']['enable_filter'] = self.enable_filter
        if self.enable_filter:
            accounts = self.env['account.account'].search([])
            data['form']['comparison'] = self._trial_balance_comparison(
                accounts)
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref(
            'base_accounting_kit.action_report_trial_balance').report_action(
            records, data=data)

    def action_print_xlsx(self):
        """Export the trial balance to xlsx (with optional comparison)."""
        self.ensure_one()
        data = self.pre_print_report(self._xlsx_base_data())
        report_model = self.env[
            'report.base_accounting_kit.report_trial_balance']
        accounts = self.env['account.account'].search([])
        account_res = report_model.with_context(
            data['form']['used_context'])._get_accounts(
            accounts, data['form']['display_account'])
        cmp_balances = self._trial_balance_comparison(accounts)

        columns = [
            {'label': 'Code', 'width': 12},
            {'label': 'Account', 'width': 45},
            {'label': 'Debit', 'width': 16, 'num': True},
            {'label': 'Credit', 'width': 16, 'num': True},
            {'label': 'Balance', 'width': 16, 'num': True},
        ]
        if self.enable_filter:
            columns += [
                {'label': 'Comparison Balance', 'width': 18, 'num': True},
                {'label': 'Variance', 'width': 16, 'num': True},
            ]
        rows = []
        tot_debit = tot_credit = tot_balance = 0.0
        for account in account_res:
            cells = [account['code'], account['name'], account['debit'],
                     account['credit'], account['balance']]
            tot_debit += account['debit']
            tot_credit += account['credit']
            tot_balance += account['balance']
            if self.enable_filter:
                cmp_bal = cmp_balances.get(account['code'], 0.0)
                cells += [cmp_bal, account['balance'] - cmp_bal]
            rows.append({'cells': cells})
        total_cells = ['', 'Total', tot_debit, tot_credit, tot_balance]
        if self.enable_filter:
            total_cells += ['', '']
        rows.append({'cells': total_cells, 'bold': True})
        table = {
            'title': 'Trial Balance',
            'meta': self._xlsx_meta(data['form']),
            'columns': columns,
            'rows': rows,
        }
        return self._xlsx_action('Trial Balance', table)
