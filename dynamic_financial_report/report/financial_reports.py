# -*- coding: utf-8 -*-
import time
from odoo import api, models, _
from odoo.exceptions import UserError


class InsReportBalanceSheet(models.AbstractModel):
    _name = 'report.dynamic_financial_report.balance_sheet'

    @api.model
    def _get_report_values(self, docids, data=None):
        if self.env.context.get('js_report'):
            if data.get('report_data'):
                data.update({
                    'Filters': data.get('report_data')[0],
                    'account_data': data.get('report_data')[1],
                    'report_lines': data.get('report_data')[2],
                    'report_name': data.get('report_name')
                })

        return data
