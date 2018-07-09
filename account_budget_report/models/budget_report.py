# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jesni Banu(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
from odoo import models, fields


class AccountBudgetAnalytic(models.TransientModel):
    _name = 'account.budget.report'
    _description = 'Account Budget report for analytic account'

    date_from = fields.Date('Start of period', required=True, default=lambda *a: time.strftime('%Y-01-01'))
    date_to = fields.Date('End of period', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))

    def check_report(self):
        active_ids = self.env.context.get('active_ids', [])
        data = self.read()[0]
        datas = {
            'ids': active_ids,
            'model': 'account.budget.post',
            'form': data
        }
        datas['form']['ids'] = datas['ids']
        datas['form']['report'] = 'analytic-full'
        return self.env['report'].get_action([], 'account_budget_report.report_budget', data=datas)


