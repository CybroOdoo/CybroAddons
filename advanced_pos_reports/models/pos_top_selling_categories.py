from odoo import api, fields, models, tools, _
from odoo.osv.expression import AND


class ReportPosCategories(models.AbstractModel):
    _name = 'report.advanced_pos_reports.report_pos_top_selling_categories'

    def get_top_selling_categories_details(self, no_of_categories=False, start_date=False, end_date=False):
        order_ids = self.env["pos.order"].search([('date_order', '>=', start_date),
                                                  ('date_order', '<=', end_date), ('state', 'in', ['paid', 'done', 'invoiced'])])
        user_currency = self.env.company.currency_id
        if order_ids:
            self.env.cr.execute("""SELECT category.name,
                sum(price_subtotal_incl) as amount FROM pos_order_line AS line,
                pos_category AS category, product_product AS product INNER JOIN
                product_template AS template ON product.product_tmpl_id = template.id WHERE line.product_id = product.id
                AND template.pos_categ_id = category.id
                AND line.order_id IN %s
                GROUP BY category.name ORDER BY amount DESC LIMIT %s
                """, (tuple(order_ids.ids), no_of_categories))
            categories = self.env.cr.dictfetchall()
        return {
            'categories': categories or [],
            'today': fields.Datetime.now(),
            'start_date': start_date,
            'end_date': end_date
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        data.update(self.get_top_selling_categories_details(data['no_of_categories'], data['start_date'],
                                                      data['end_date']))
        return data