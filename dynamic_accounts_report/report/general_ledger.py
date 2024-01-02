# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, models, _


class GeneralLedger(models.AbstractModel):
    _name = 'report.dynamic_accounts_report.general_ledger'

    @api.model
    def _get_report_values(self, docids, data=None):

        if self.env.context.get('trial_pdf_report'):

            if data.get('report_data'):
                data.update(
                    {'account_data': data.get('report_data')['report_lines'],
                     'Filters': data.get('report_data')['filters'],
                     'debit_total': data.get('report_data')['debit_total'],
                     'credit_total': data.get('report_data')['credit_total'],
                     'title': data.get('report_data')['name'],
                     'company': self.env.company,
                     })
        return data
