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
from odoo import _, fields, models

from .report_company import get_report_branches


class DynamicTrialBalance(models.AbstractModel):
    """Trial Balance: figures from ``report_trial_balance._get_accounts``
    (opening balances per fiscal year, Result Brought Forward), journal
    items of an account from the General Ledger computation."""
    _name = 'account.dynamic.report.trial_balance'
    _inherit = 'account.dynamic.report'
    _description = 'Trial Balance'

    _filters = ('date', 'comparison', 'target_move', 'journals')
    _comparison = True
    _columns_by = True

    def _report_title(self):
        return _("Trial Balance")

    def _option_defs(self):
        return [{'key': 'display_account', 'label': _("Display Accounts"),
                 'type': 'select', 'default': 'movement',
                 'values': {'movement': _("With movements"),
                            'all': _("All accounts"),
                            'not_zero': _("With balance not equal to 0")}}]

    def _columns(self, options):
        if options['columns_by']:
            # Initial Balance, then the balance at the end of each period
            # (each column is a trial balance; the last one the end balance)
            columns = self._kit_period_column_defs(
                self._kit_period_columns(self.env.company, options))
            for column in columns:
                # an amount opens the ledger from the start of the period
                column['date_from'] = fields.Date.to_string(options['date_from'])
            return [{'name': _("Initial Balance"), 'type': 'monetary'}] + columns
        columns = [{'name': _("Initial Balance"), 'type': 'monetary'},
                   {'name': _("Debit"), 'type': 'monetary'},
                   {'name': _("Credit"), 'type': 'monetary'},
                   {'name': _("End Balance"), 'type': 'monetary'}]
        periods = self._comparison_periods(self.env.company, options)
        if periods:
            columns.append({'name': _("Balance"), 'type': 'monetary'})
            columns += [{'name': label, 'type': 'monetary'}
                        for _from, _to, label in periods]
            columns.append({'name': _("Variance"), 'type': 'monetary'})
        return columns

    def _accounts(self):
        return self.env['account.account'].search(
            self.env['account.account']._check_company_domain(
                self.env.company))

    def _report_accounts(self, options):
        """Accounts shown: those of the Accounts filter, if the report has
        one and accounts are chosen, else all of them."""
        accounts = self._accounts()
        if options.get('account_ids'):
            accounts = accounts.filtered(
                lambda a: a.id in options['account_ids'])
        return accounts

    def _lines(self, options):
        accounts = self._report_accounts(options)
        report = self.env['report.base_accounting_kit.report_trial_balance']
        rows = report.with_context(**self._report_context(options))\
            ._get_accounts(accounts, options['display_account'])
        compared = []
        by_period = self._kit_period_columns(self.env.company, options)
        for date_from, date_to, _label in by_period or self._comparison_periods(
                self.env.company, options):
            if by_period:
                # balance at the period end: from the report start, opening
                # balance included
                res = report.with_context(**self._report_context(
                    options, options['date_from'], date_to))._get_accounts(accounts, 'all')
                # (the Result Brought Forward line has no account: 'rbf')
                compared.append({r.get('id') or 'rbf': r['end_balance'] for r in res})
                continue
            res = report.with_context(**self._report_context(
                options, date_from, date_to))._get_accounts(accounts, 'all')
            compared.append({r['id']: r['balance'] for r in res
                             if r.get('id')})
        lines = []
        # the Trial Balance's own columns (the General Ledger maps them)
        totals = [0.0] * (len(compared) + 1 if by_period
                          else 4 + (len(compared) + 2 if compared else 0))
        for row in rows:
            columns = [row['init_balance'], row['debit'], row['credit'],
                       row['end_balance']]
            if by_period:
                columns = [row['init_balance']] + [
                    period.get(row.get('id') or 'rbf', 0.0) for period in compared]
            elif compared:
                previous = [period.get(row.get('id'), 0.0)
                            for period in compared]
                columns += [row['balance']] + previous \
                    + [row['balance'] - previous[0]]
            totals = [t + c for t, c in zip(totals, columns)]
            lines.append({
                'id': 'account_%s' % row['id'] if row.get('id') else 'rbf',
                'name': ('%s %s' % (row['code'], row['name'])).strip(),
                'level': 0,
                'columns': columns,
                'unfoldable': bool(row.get('id')),
            })
        lines.append({'id': 'total', 'name': _("Total"), 'level': 0,
                      'columns': totals, 'class': 'total'})
        return lines

    def _ledger_items(self, options, line_id, init_balance=True,
                      sortby='sort_date'):
        """Journal items of an unfolded account, from the General Ledger
        computation (opening line, running balance)."""
        if not line_id.startswith('account_'):
            return []
        account = self.env['account.account'].browse(
            int(line_id.split('_')[1])).exists()
        if not account:
            return []
        ledger = self.env[
            'report.base_accounting_kit.report_general_ledger'].with_context(
            **self._report_context(options))
        res = ledger._get_account_move_entry(account, init_balance, sortby,
                                             'all')
        items = []
        for item in (res[0]['move_lines'] if res else []):
            items.append({
                'id': 'aml_%s' % item['lid'] if item.get('lid')
                else 'init_%s' % account.id,
                'name': ' - '.join(str(v) for v in (
                    item.get('ldate'), item.get('lcode'),
                    item.get('move_name'), item.get('partner_name'),
                    item.get('lname')) if v),
                'debit': item['debit'],
                'credit': item['credit'],
                'balance': item['balance'],
                'date': fields.Date.to_date(item.get('ldate')) if item.get('ldate') else False,
            })
        if init_balance and account.account_type == 'equity_unaffected':
            # The Result Brought Forward comes from the earlier years of all
            # profit and loss accounts, not from this account's own lines.
            pl_accounts = self._accounts().filtered(
                lambda a: not a.include_initial_balance)
            _initial, rbf = ledger._get_initial_balances(pl_accounts | account)
            if rbf and rbf['account_id'] == account.id:
                for item in items:
                    item['balance'] += rbf['balance']
                items.insert(0, {'id': 'rbf_%s' % account.id,
                                 'name': _("Result Brought Forward"),
                                 'debit': rbf['debit'],
                                 'credit': rbf['credit'],
                                 'balance': rbf['balance']})
        return items

    def _child_lines(self, options, line_id):
        if options['columns_by']:
            # journal items: their running balance under their period
            # (opening lines under Initial Balance)
            periods = self._kit_period_columns(self.env.company, options)
            lines = []
            for item in self._ledger_items(options, line_id):
                columns = [''] * (len(periods) + 1)
                index = next((i + 1 for i, (start, stop, _label) in enumerate(periods)
                              if item.get('date') and start <= item['date'] <= stop), 0)
                columns[index] = item['balance']
                lines.append({'id': item['id'], 'name': item['name'], 'level': 1,
                              'parent_id': line_id, 'columns': columns})
            return lines
        blanks = [''] * (len(self._columns(options)) - 4)
        return [{'id': item['id'], 'name': item['name'], 'level': 1,
                 'parent_id': line_id,
                 'columns': ['', item['debit'], item['credit'],
                             item['balance']] + blanks}
                for item in self._ledger_items(options, line_id)]

    def _line_action(self, options, line_id):
        if line_id.startswith('aml_'):
            line = self.env['account.move.line'].browse(
                int(line_id.split('_')[1])).exists()
            if not line:
                return False
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': line.move_id.id,
                'views': [(False, 'form')],
                'target': 'current',
            }
        if not line_id.startswith('account_'):
            return False
        account = self.env['account.account'].browse(
            int(line_id.split('_')[1])).exists()
        if not account:
            return False
        if self.env.context.get('kit_period_cell'):
            # an amount of a period column: the ledger up to that period's
            # end, so its ending balance is the amount clicked (RI 3.2)
            return self._kit_ledger_action(options, account, True)
        company = self.env.company
        domain = [
            ('account_id', '=', account.id),
            ('date', '>=', fields.Date.to_string(options['date_from'])),
            ('date', '<=', fields.Date.to_string(options['date_to'])),
            ('company_id', 'in', get_report_branches(company).ids),
            ('parent_state', 'in', ['posted'] if options['target_move'] ==
             'posted' else ['draft', 'posted']),
        ] + self._kit_filter_domain(options)
        action = self.env['ir.actions.act_window']._for_xml_id(
            'account.action_account_moves_all')
        action.update({
            'name': '%s %s' % (account.code, account.name),
            'domain': domain,
            'context': {'search_default_posted': 0},
        })
        return action
