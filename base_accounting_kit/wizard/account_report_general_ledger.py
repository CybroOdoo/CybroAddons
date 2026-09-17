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
from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountReportGeneralLedger(models.TransientModel):
    _name = "account.report.general.ledger"
    _inherit = "account.common.account.report"
    _description = "General Ledger Report"

    name = fields.Char(string="General Ledger", default="General Ledger", required=True, translate=True)
    initial_balance = fields.Boolean(string='Include Initial Balances',
                                     help='If you selected date, this field '
                                          'allow you to add a row to display '
                                          'the amount of debit/credit/balance '
                                          'that precedes the filter you\'ve '
                                          'set.')
    sortby = fields.Selection(
        [('sort_date', 'Date'), ('sort_journal_partner', 'Journal & Partner')],
        string='Sort by', required=True, default='sort_date')
    journal_ids = fields.Many2many('account.journal',
                                   'account_report_general_ledger_journal_rel',
                                   'account_id', 'journal_id',
                                   string='Journals', required=True)
    enable_filter = fields.Boolean(
        string='Enable Comparison',
        help="Add a column with each account's balance over a second "
             "(comparison) period.")
    date_from_cmp = fields.Date(string='Comparison Start Date')
    date_to_cmp = fields.Date(string='Comparison End Date')

    def _general_ledger_comparison(self, accounts):
        """Return ``{account_code: balance}`` for the comparison period."""
        if not self.enable_filter:
            return {}
        by_id = self._period_account_balances(
            accounts, self.date_from_cmp, self.date_to_cmp)
        return {a.code: by_id[a.id] for a in accounts if a.id in by_id}

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        if data['form'].get('initial_balance') and not data['form'].get(
                'date_from'):
            raise UserError(_("You must define a Start Date"))
        data['form']['enable_filter'] = self.enable_filter
        if self.enable_filter:
            data['form']['comparison'] = self._general_ledger_comparison(
                self.env['account.account'].search([]))
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref(
            'base_accounting_kit.action_report_general_ledger').with_context(
            landscape=True).report_action(records, data=data)

    def action_print_xlsx(self):
        """Export the general ledger to xlsx (mirrors the PDF, with an
        optional per-account comparison-period balance)."""
        self.ensure_one()
        data = self.pre_print_report(self._xlsx_base_data())
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        if data['form'].get('initial_balance') and not data['form'].get(
                'date_from'):
            raise UserError(_("You must define a Start Date"))
        report_model = self.env[
            'report.base_accounting_kit.report_general_ledger']
        accounts = self.env['account.account'].search([])
        accounts_res = report_model.with_context(
            data['form']['used_context'])._get_account_move_entry(
            accounts, data['form'].get('initial_balance'),
            data['form'].get('sortby'), data['form']['display_account'])
        cmp_balances = self._general_ledger_comparison(accounts)

        columns = [
            {'label': 'Date', 'width': 12},
            {'label': 'JRNL', 'width': 8},
            {'label': 'Partner', 'width': 28},
            {'label': 'Ref', 'width': 28},
            {'label': 'Move', 'width': 16},
            {'label': 'Debit', 'width': 16, 'num': True},
            {'label': 'Credit', 'width': 16, 'num': True},
            {'label': 'Balance', 'width': 16, 'num': True},
        ]
        if self.enable_filter:
            columns.append(
                {'label': 'Comparison Balance', 'width': 18, 'num': True})
        rows = []
        for account in accounts_res:
            head = ['%s %s' % (account['code'], account['name']),
                    '', '', '', '', account['debit'], account['credit'],
                    account['balance']]
            if self.enable_filter:
                head.append(cmp_balances.get(account['code'], 0.0))
            rows.append({'cells': head, 'bold': True})
            for line in account['move_lines']:
                cells = [line.get('ldate'), line.get('lcode'),
                         line.get('partner_name') or '', line.get('lname') or '',
                         line.get('move_name') or '', line.get('debit'),
                         line.get('credit'), line.get('balance')]
                if self.enable_filter:
                    cells.append('')
                rows.append({'cells': cells, 'indent': 1})
        table = {
            'title': 'General Ledger',
            'meta': self._xlsx_meta(data['form']),
            'columns': columns,
            'rows': rows,
        }
        return self._xlsx_action('General Ledger', table)
