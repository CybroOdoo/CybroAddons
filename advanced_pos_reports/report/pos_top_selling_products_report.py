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

        product_summary = []
        if order_ids:
            query = """
                SELECT product.id, template.name, uom.name AS uom, 
                       product.default_code AS code, sum(line.qty) AS qty, 
                       sum(line.price_subtotal_incl) AS total
                FROM product_product AS product
                JOIN pos_order_line AS line ON product.id = line.product_id
                JOIN product_template AS template ON product.product_tmpl_id = template.id
                LEFT JOIN uom_uom AS uom ON template.uom_id = uom.id
                WHERE line.order_id IN %s 
                GROUP BY product.id, template.name, product.default_code, uom.name
                ORDER BY qty DESC
            """
            if no_of_products and no_of_products > 0:
                query += " LIMIT %s"
                self.env.cr.execute(query, (tuple(order_ids.ids), no_of_products))
            else:
                self.env.cr.execute(query, (tuple(order_ids.ids),))

            for row in self.env.cr.dictfetchall():
                name = row['name']
                if isinstance(name, dict):
                    name = name.get(self.env.lang) or name.get('en_US') or next(iter(name.values()), '')
                row['name'] = name

                uom = row['uom']
                if isinstance(uom, dict):
                    uom = uom.get(self.env.lang) or uom.get('en_US') or next(iter(uom.values()), '')
                row['uom'] = uom or ''

                product_summary.append(row)

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
            self.get_top_selling_products_details(data.get('no_of_products'),
                                                  data.get('start_date'),
                                                  data.get('end_date')))
        return data
