# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ReportPosTopSellingProducts(models.AbstractModel):
    """Generate top_selling products from pos"""
    _name = 'report.advanced_pos_reports.report_pos_top_selling_products'
    _description = "Report for POS Top Selling Products"

    def get_top_selling_products_details(self,
                                         no_of_products=None,
                                         start_date=False, end_date=False):
        """Get top_selling products details"""
        order_ids = self.env["pos.order"].search(
            [('date_order', '>=', start_date),
             ('date_order', '<=', end_date),
             ('state', 'in', ['paid', 'done', 'invoiced'])])

        if order_ids:
            query = """
                SELECT product.id, template.name, uom.name AS uom, 
                       product.default_code as code, sum(qty) as qty, 
                       sum(line.price_subtotal_incl) as total FROM 
                       product_product AS product, pos_order_line AS line, 
                       product_template AS template , uom_uom AS uom WHERE 
                       product.id = line.product_id AND 
                       template.id = product.product_tmpl_id AND 
                       uom.id = template.uom_id AND line.order_id IN %s 
                       GROUP BY product.id, template.name, 
                       template.default_code, uom.name ORDER BY qty DESC
                """
            if no_of_products > 0:
                query += " LIMIT %s"
                self.env.cr.execute(query,
                                    (tuple(order_ids.ids), no_of_products))
            else:
                self.env.cr.execute(query, (tuple(order_ids.ids),))

        product_summary = self.env.cr.dictfetchall()

        return {
            'products': product_summary,
            'today': fields.Datetime.now(),
            'start_date': start_date,
            'end_date': end_date
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get report values"""
        data = dict(data or {})
        data.update(
            self.get_top_selling_products_details(data['no_of_products'],
                                                  data['start_date'],
                                                  data['end_date']))
        return data
