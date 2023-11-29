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


class ReportPosTopSellingCategories(models.AbstractModel):
    """Generate top_selling categories report"""
    _name = 'report.advanced_pos_reports.report_pos_top_selling_categories'
    _description = "Report for Top Selling POS Categories"

    def get_top_selling_categories_details(self, no_of_categories=None,
                                           start_date=False, end_date=False):
        """Get top_selling categories details"""
        order_ids = self.env["pos.order"].search(
            [('date_order', '>=', start_date),
             ('date_order', '<=', end_date),
             ('state', 'in', ['paid', 'done', 'invoiced'])])
        if order_ids:
            query = """
                       SELECT category.name, sum(price_subtotal_incl) as amount
                        FROM pos_order_line AS line,pos_category AS category, 
                        product_product AS product INNER JOIN
                        product_template AS template ON 
                        product.product_tmpl_id = template.id WHERE 
                        line.product_id = product.id
                        AND template.pos_categ_id = category.id
                        AND line.order_id IN %s
                        GROUP BY category.name ORDER BY amount DESC
            """
            if no_of_categories > 0:
                query += " LIMIT %s"
                self.env.cr.execute(query,
                                    (tuple(order_ids.ids), no_of_categories))
            else:
                self.env.cr.execute(query, (tuple(order_ids.ids),))
        categories = self.env.cr.dictfetchall()
        return {
            'categories': categories or [],
            'today': fields.Datetime.now(),
            'start_date': start_date,
            'end_date': end_date
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get report values"""
        data = dict(data or {})
        data.update(
            self.get_top_selling_categories_details(data['no_of_categories'],
                                                    data['start_date'],
                                                    data['end_date']))
        return data
