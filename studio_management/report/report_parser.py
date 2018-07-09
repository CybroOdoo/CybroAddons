from datetime import date
from odoo import api, models


class ParticularReport(models.AbstractModel):
    _name = 'report.studio_management.report_digital_studio'

    @api.model
    def render_html(self, docids, data=None):
        records = self.env['session.details'].search([])
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('studio_management.report_digital_studio')
        if data['form']['date_from'] and data['form']['date_to'] and data['form']['customer_id']:
            records = self.env['session.details'].search([('customer_id', '=', data['form']['customer_id'][0]),
                                                          ('return_date', '>=', data['form']['date_from']),
                                                          ('return_date', '<=', data['form']['date_to'])])
        elif data['form']['date_from'] and data['form']['date_to']:
            records = self.env['session.details'].search([('return_date', '>=', data['form']['date_from']),
                                                          ('return_date', '<=', data['form']['date_to'])])
        elif data['form']['date_to'] and data['form']['customer_id']:
            records = self.env['session.details'].search([('customer_id', '=', data['form']['customer_id'][0]),
                                                          ('return_date', '<=', data['form']['date_to'])])
        elif data['form']['date_from'] and data['form']['customer_id']:
            records = self.env['session.details'].search([('customer_id', '=', data['form']['customer_id'][0]),
                                                          ('return_date', '>=', data['form']['date_from'])])
        elif data['form']['date_from']:
            records = self.env['session.details'].search([('return_date', '>=', data['form']['date_from'])])
        elif data['form']['date_to']:
            records = self.env['session.details'].search([('return_date', '<=', data['form']['date_to'])])
        elif data['form']['customer_id']:
            records = self.env['session.details'].search([('customer_id', '=', data['form']['customer_id'][0])])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'records': records,
            'date_cur': date.today(),
            'docs': self,
        }
        return report_obj.render('studio_management.report_digital_studio', docargs)
