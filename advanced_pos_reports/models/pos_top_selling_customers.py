from odoo import api, fields, models


class ReportPosCustomers(models.AbstractModel):
    _name = 'report.advanced_pos_reports.report_pos_top_selling_customers'

    def get_top_selling_customers_details(self, no_of_customers=False, start_date=False, end_date=False):
        order_ids = self.env["pos.order"].search([('date_order', '>=', start_date),
                                                  ('date_order', '<=', end_date),
                                                  ('state', 'in', ['paid', 'done', 'invoiced'])])
        user_currency = self.env.company.currency_id
        if order_ids:
            self.env.cr.execute("""SELECT partner.id, partner.name,
                            sum(amount_total) as amount FROM pos_order, res_partner AS partner 
                            WHERE partner.id= pos_order.partner_id AND pos_order.id IN %s 
                            GROUP BY partner.id, partner.name ORDER BY amount DESC LIMIT %s 
                            """, (tuple(order_ids.ids), no_of_customers))
            customers = self.env.cr.dictfetchall()
        return {
            'customers': customers or [],
            'today': fields.Datetime.now(),
            'start_date': start_date,
            'end_date': end_date
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        data.update(self.get_top_selling_customers_details(data['no_of_customers'], data['start_date'],
                                                           data['end_date']))
        return data
