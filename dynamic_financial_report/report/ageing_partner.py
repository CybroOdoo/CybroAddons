from odoo import api, models


class InsReportAgeingPartner(models.AbstractModel):
    _name = 'report.dynamic_financial_report.ageing_partner'

    @api.model
    def _get_report_values(self, docids, data=None):
        """ fetch values for get pdf report"""
        if self.env.context.get('js_report'):
            if data.get('report_data'):
                data.update({'account_data': data.get('report_data')[1],
                             'Filters': data.get('report_data')[0],
                             })
        return data
