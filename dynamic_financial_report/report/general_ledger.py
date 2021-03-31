# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class InsReportGeneralLedger(models.AbstractModel):
    _name = 'report.dynamic_financial_report.general_ledger'
    @api.model
    def _get_report_values(self, docids, data=None):
        if self.env.context.get('js_report'):
            if data.get('report_data'):
                data.update({'account_data': data.get('report_data')[1],
                             'Filters': data.get('report_data')[0],
                             })
        return data


class InsReportTrialBalance(models.AbstractModel):
    _name = 'report.dynamic_financial_report.trial_balance'

    @api.model
    def _get_report_values(self, docids, data=None):
        if self.env.context.get('js_report'):

            if data.get('report_data'):
                data.update({'account_data': data.get('report_data')[1],
                             'Filters': data.get('report_data')[0],
                             'total': data.get('report_data')[2],
                             })
        return data
