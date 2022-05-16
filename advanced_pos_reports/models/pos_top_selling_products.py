from odoo import api, fields, models, tools, _
from odoo.osv.expression import AND


class ReportPosProducts(models.AbstractModel):
    _name = 'report.advanced_pos_reports.report_pos_top_selling_products'

    def get_top_selling_products_details(self, no_of_products=False, start_date=False, end_date=False):
        order_ids = self.env["pos.order"].search([('date_order', '>=', start_date),
                                                  ('date_order', '<=', end_date), ('state', 'in', ['paid', 'done', 'invoiced'])])
        user_currency = self.env.company.currency_id
        categories = []
        if order_ids:
            self.env.cr.execute("""
                                SELECT product.id, template.name, uom.name AS uom, product.default_code as code, sum(qty) as qty, sum(line.price_subtotal_incl) as total
                                FROM product_product AS product,
                                     pos_order_line AS line, product_template AS template , uom_uom AS uom
                                WHERE product.id = line.product_id AND template.id = product.product_tmpl_id AND uom.id = template.uom_id
                                    AND line.order_id IN %s
                                GROUP BY product.id, template.name, template.default_code, uom.name ORDER BY qty DESC LIMIT %s
                                """, (tuple(order_ids.ids), no_of_products))
            product_summary = self.env.cr.dictfetchall()
        return {
            'products': product_summary,
            'today': fields.Datetime.now(),
            'start_date': start_date,
            'end_date': end_date
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        data.update(self.get_top_selling_products_details(data['no_of_products'], data['start_date'],
                                                      data['end_date']))
        return data