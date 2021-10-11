from odoo import api, models, _


class GeneralLedger(models.AbstractModel):
    _name = 'report.dynamic_accounts_report.general_ledger'

    @api.model
    def _get_report_values(self, docids, data=None):

        if self.env.context.get('trial_pdf_report'):

            if data.get('report_data'):
                data.update({'account_data': data.get('report_data')['report_lines'],
                             'Filters': data.get('report_data')['filters'],
                             'debit_total': data.get('report_data')['debit_total'],
                             'credit_total': data.get('report_data')['credit_total'],
                             'title': data.get('report_data')['name'],
                             'company': self.env.company,
                             })
        return data
