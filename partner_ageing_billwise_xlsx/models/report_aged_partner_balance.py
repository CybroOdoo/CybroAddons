# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, _
from odoo.exceptions import UserError


class AgedTrialBalanceBillwise(models.TransientModel):
    _name = 'account.aged.trial.balance.xls'
    _inherit = 'account.aged.trial.balance'
    _description = 'Account Aged Trial balance Report Bill-wise'

    def _print_report(self, data):
        res = {}
        data = self.pre_print_report(data)

        data['form'].update(self.read(['period_length'])[0])
        period_length = data['form']['period_length']
        if period_length <= 0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))

        start = datetime.strptime(data['form']['date_from'], "%Y-%m-%d")

        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i != 0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        data['form'].update(res)

        return {
            'name': 'Aged Partner Balance Excel',
            'type': 'ir.actions.report.xml',
            'report_name': 'partner_ageing_billwise_xlsx.partner_balance_xlsx.xlsx',
            'datas': data
        }
