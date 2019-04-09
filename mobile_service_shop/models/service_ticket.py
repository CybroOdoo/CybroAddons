from odoo import models, api


class StockMoveReport(models.AbstractModel):

    _name = 'report.mobile_service_shop.mobile_service_ticket_template'

    @api.model
    def _get_report_values(self, docids, data):
        terms = self.env['terms.conditions'].search([])
        return {
            'date_today': data['date_today'],
            'date_request': data['date_request'],
            'date_return': data['date_return'],
            'sev_id': data['sev_id'],
            'imei_no': data['imei_no'],
            'technician': data['technician'],
            'complaint_types': data['complaint_types'],
            'complaint_description': data['complaint_description'],
            'mobile_brand': data['mobile_brand'],
            'model_name': data['model_name'],
            'customer_name': data['customer_name'],
            'warranty': data['warranty'],
            'terms': terms,
        }

