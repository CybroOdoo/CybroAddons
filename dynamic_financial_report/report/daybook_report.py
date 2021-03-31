# -*- coding: utf-8 -*-
from odoo import api, models, _


class InsReportDayBook(models.AbstractModel):
    _name = 'report.dynamic_financial_report.dynamic_day_book'

    @api.model
    def _get_report_values(self, docids, data=None):
        """ fetch values for get pdf report"""
        if self.env.context.get('js_report'):
            if data.get('report_data'):
                data.update({'account_data': data.get('report_data')[1],
                             'Filters': data.get('report_data')[0],
                             'lines': data.get('report_data')[2],
                             })

        return data
