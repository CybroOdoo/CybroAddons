from odoo import api, models, _


class PartnerLedgerReport(models.AbstractModel):
    _name = 'report.dynamic_accounts_report.partner_ledger'

    @api.model
    def _get_report_values(self, docids, data=None):
        if self.env.context.get('partner_ledger_pdf_report'):

            if data.get('report_data'):
                data.update({'account_data': data.get('report_data')['report_lines'],
                             'Filters': data.get('report_data')['filters'],
                             'company': self.env.company,
                             })
        return data
