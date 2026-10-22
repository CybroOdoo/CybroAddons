# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
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
        categories = []
        if order_ids:
            query = """
                SELECT category.name, sum(line.price_subtotal_incl) AS amount
                FROM pos_order_line AS line 
                INNER JOIN product_product AS product ON line.product_id = product.id 
                INNER JOIN product_template AS template ON product.product_tmpl_id = template.id
                INNER JOIN pos_category_product_template_rel AS categ ON product.product_tmpl_id = categ.product_template_id
                INNER JOIN pos_category AS category ON categ.pos_category_id = category.id
                WHERE line.order_id IN %s
                GROUP BY category.name
                ORDER BY amount DESC 
            """
            if no_of_categories and no_of_categories > 0:
                query += " LIMIT %s"
                self.env.cr.execute(query, (tuple(order_ids.ids), no_of_categories))
            else:
                self.env.cr.execute(query, (tuple(order_ids.ids),))

            for row in self.env.cr.dictfetchall():
                name = row['name']
                if isinstance(name, dict):
                    name = name.get(self.env.lang) or name.get('en_US') or next(iter(name.values()), '')
                row['name'] = name
                categories.append(row)

        return {
            'categories': categories,
            'today': fields.Datetime.now(),
            'start_date': start_date,
            'end_date': end_date
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get report values"""
        data = dict(data or {})
        data.update(
            self.get_top_selling_categories_details(data.get('no_of_categories'),
                                                    data.get('start_date'),
                                                    data.get('end_date')))
        return data
