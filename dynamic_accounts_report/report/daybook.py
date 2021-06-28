from odoo import api, models, _


class DayBook(models.AbstractModel):
    _name = 'report.dynamic_accounts_report.day_book'

    @api.model
    def _get_report_values(self, docids, data=None):

        if self.env.context.get('daybook_pdf_report'):

            if data.get('report_data'):
                data.update({'account_data': data.get('report_data')['report_lines'],
                             'Filters': data.get('report_data')['filters'],
                             'company': self.env.company,
                             })
        return data