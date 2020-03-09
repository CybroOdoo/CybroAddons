# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ijaz Ahammed, Varsha Vivek (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models


class AccountingReport(models.TransientModel):
    _name = "accounting.report"
    _inherit = "account.common.report"
    _description = "Accounting Report"

    @api.model
    def _get_account_report(self):
        reports = []
        if self._context.get('active_id'):
            menu = self.env['ir.ui.menu'].browse(self._context.get('active_id')).name
            reports = self.env['account.financial.report'].search([('name', 'ilike', menu)])
        return reports and reports[0] or False

    account_report_id = fields.Many2one('account.financial.report', string='Account Reports', required=True,
                                        default=_get_account_report)

    debit_credit = fields.Boolean(string='Enable Debit/Credit',
                                  help="This option allows you to get more details about the way"
                                       " your balances are computed. Because it is space consuming,"
                                       " we do not allow to use it while doing a comparison.")

    def _build_comparison_context(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        return result

    @api.multi
    def check_report(self):
        res = super(AccountingReport, self).check_report()
        data = {}
        data['form'] = \
            self.read(
                ['account_report_id', 'journal_ids', 'target_move'])[0]
        for field in ['account_report_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        comparison_context = self._build_comparison_context(data)
        res['data']['form']['comparison_context'] = comparison_context
        return res

    def _print_report(self, data):
        data['form'].update(self.read(
            ['debit_credit', 'account_report_id', 'target_move'])[0])
        return self.env.ref('cash_flow_statement.action_report_financial').report_action(self, data=data, config=False)
