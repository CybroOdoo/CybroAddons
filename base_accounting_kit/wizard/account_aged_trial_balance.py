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
import time
from dateutil.relativedelta import relativedelta
from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountAgedTrialBalance(models.TransientModel):
    _name = 'account.aged.trial.balance'
    _inherit = 'account.common.partner.report'
    _description = 'Account Aged Trial balance Report'

    name = fields.Char(string="Account Aged Trial balance Report", default="Account Aged Trial balance Report", required=True, translate=True)

    journal_ids = fields.Many2many('account.journal', string='Journals',
                                   required=True)
    period_length = fields.Integer(string='Period Length (days)',
                                   required=True, default=30)
    date_from = fields.Date(default=lambda *a: time.strftime('%Y-%m-%d'))

    def _print_report(self, data):
        res = {}
        data = self.pre_print_report(data)
        data['form'].update(self.read(['period_length'])[0])
        period_length = data['form']['period_length']
        if period_length <= 0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))

        start = data['form']['date_from']

        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i != 0 and (
                            str((5 - (i + 1)) * period_length) + '-' + str(
                        (5 - i) * period_length)) or (
                                     '+' + str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        data['form'].update(res)
        return self.env.ref(
            'base_accounting_kit.action_report_aged_partner_balance').with_context(
            landscape=True).report_action(self, data=data)

    def _aged_buckets(self, data):
        """Replicate the aging bucket definitions built by ``_print_report``."""
        res = {}
        period_length = data['form']['period_length']
        start = data['form']['date_from']
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i != 0 and (
                    str((5 - (i + 1)) * period_length) + '-' + str(
                        (5 - i) * period_length)) or (
                    '+' + str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        return res

    def action_print_xlsx(self):
        """Export the aged partner balance to xlsx."""
        self.ensure_one()
        data = self.pre_print_report(self._xlsx_base_data())
        data['form'].update(self.read(['period_length'])[0])
        period_length = data['form']['period_length']
        if period_length <= 0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))
        buckets = self._aged_buckets(data)
        data['form'].update(buckets)
        if data['form']['result_selection'] == 'customer':
            account_type = ['asset_receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['liability_payable']
        else:
            account_type = ['liability_payable', 'asset_receivable']
        report_model = self.env[
            'report.base_accounting_kit.report_agedpartnerbalance']
        movelines, total, _lines = report_model._get_partner_move_lines(
            account_type, str(data['form']['date_from']),
            data['form'].get('target_move', 'all'), period_length)

        columns = [{'label': 'Partner', 'width': 40},
                   {'label': 'Not Due', 'width': 14, 'num': True}]
        for key in ('4', '3', '2', '1', '0'):
            columns.append(
                {'label': buckets[key]['name'], 'width': 14, 'num': True})
        columns.append({'label': 'Total', 'width': 16, 'num': True})
        rows = []
        for partner in movelines:
            rows.append({'cells': [
                partner['name'], partner['direction'], partner['4'],
                partner['3'], partner['2'], partner['1'], partner['0'],
                partner['total'],
            ]})
        rows.append({'cells': [
            'Account Total', total[6], total[4], total[3], total[2],
            total[1], total[0], total[5],
        ], 'bold': True})
        table = {
            'title': 'Aged Partner Balance',
            'meta': self._xlsx_meta(data['form']),
            'columns': columns,
            'rows': rows,
        }
        return self._xlsx_action('Aged Partner Balance', table)
