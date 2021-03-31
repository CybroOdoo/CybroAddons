# -*- coding: utf-8 -*-

from odoo import api, models


class InsReportPartnerLedger(models.AbstractModel):
    _name = 'report.dynamic_financial_report.partner_ledger'

    @api.model
    def _get_report_values(self, docids, data=None):
        if self.env.context.get('js_report'):
            if data.get('report_data'):
                data.update({'account_data': data.get('report_data')[1],
                             'Filters': data.get('report_data')[0],
                             })
        return data
