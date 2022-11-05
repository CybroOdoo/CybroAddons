from odoo import api, models, _


class PartnerAgeing(models.AbstractModel):
    _name = 'report.dynamic_accounts_report.partner_ageing'

    @api.model
    def _get_report_values(self, docids, data=None):
        if self.env.context.get('ageing_pdf_report'):

            if data.get('report_data'):
                data.update(
                    {'account_data': data.get('report_data')['report_lines'][0],
                     'Filters': data.get('report_data')['filters'],
                     'company': self.env.company,

                     })

        return data
