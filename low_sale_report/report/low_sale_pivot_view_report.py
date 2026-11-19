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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class LowSalePivotViewReport(models.Model):
    """Temporary model storing low sales report records for pivot visualization."""

    _name = 'low.sale.pivot.view.report'
    _description = 'Low Sales Pivot View Report'

    categ_id = fields.Many2one(
        comodel_name='product.category',
        string="Product Category",
        readonly=True,
        help="Category ID of the product",
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product Variant",
        readonly=True,
        help="Product variant record",
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string="Product",
        readonly=True,
        help="Product template record",
    )
    product_uom_qty = fields.Float(
        string="Sold quantity",
        readonly=True,
        help="Total count of the quantity sold",
    )
    company_id = fields.Many2one(
        'res.company',
        store=True,
        copy=False,
        default=lambda self: self.env.company.id,
        help="Company reference for monetary evaluation",
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        help="Currency reference for monetary amounts",
    )
    price_total = fields.Monetary(
        string="Total",
        readonly=True,
        help="Total price of the product sold",
    )

    def get_data(self, low_sale_report):
        """Fetch low sales data using parameterized SQL queries for pivot and Excel reports."""
        params = []
        where_clauses = []
        having_clauses = []

        start_date = low_sale_report.get('analysed_period_start')
        end_date = low_sale_report.get('analysed_period_end')
        if start_date and end_date:
            where_clauses.append("(o.date_order BETWEEN %s AND %s OR o.id IS NULL)")
            params.extend([f"{start_date} 00:00:00", f"{end_date} 23:59:59"])

        category = low_sale_report.get('category')
        if category:
            categ_id = (
                category.id
                if hasattr(category, 'id')
                else (category[0] if isinstance(category, (list, tuple)) else category)
            )
            if categ_id:
                where_clauses.append("t.categ_id = %s")
                params.append(int(categ_id))

        sale_team = low_sale_report.get('sale_team')
        if sale_team:
            team_id = (
                sale_team.id
                if hasattr(sale_team, 'id')
                else (sale_team[0] if isinstance(sale_team, (list, tuple)) else sale_team)
            )
            if team_id:
                where_clauses.append("(o.team_id = %s OR o.id IS NULL)")
                params.append(int(team_id))

        absolute_qty = low_sale_report.get('absolute_qty') or 0.0
        if absolute_qty > 0:
            having_clauses.append(
                "COALESCE(SUM(CASE WHEN o.state = 'sale' "
                "THEN l.product_uom_qty ELSE 0 END), 0) <= %s"
            )
            params.append(float(absolute_qty))

        where_sql = (' WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''
        having_sql = (' HAVING ' + ' AND '.join(having_clauses)) if having_clauses else ''

        if low_sale_report.get('product_type') == 'variant':
            query = f"""
                SELECT
                    p.id AS product_id,
                    COALESCE(
                        SUM(CASE WHEN o.state = 'sale' THEN l.product_uom_qty ELSE 0 END), 0
                    ) AS total_sold_quantity,
                    COALESCE(
                        SUM(CASE WHEN o.state = 'sale' THEN l.price_total ELSE 0 END), 0
                    ) AS price_total,
                    COALESCE(t.name->>'en_US', t.name->>'en_GB', t.name::text) AS product_name
                FROM
                    product_product p
                LEFT JOIN
                    product_template t ON p.product_tmpl_id = t.id
                LEFT JOIN
                    sale_order_line l ON p.id = l.product_id
                LEFT JOIN
                    sale_order o ON l.order_id = o.id
                {where_sql}
                GROUP BY
                    p.id, t.name
                {having_sql}
            """
        else:
            query = f"""
                SELECT
                    t.id AS product_tmpl_id,
                    COALESCE(
                        SUM(CASE WHEN o.state = 'sale' THEN l.product_uom_qty ELSE 0 END), 0
                    ) AS total_sold_quantity,
                    COALESCE(
                        SUM(CASE WHEN o.state = 'sale' THEN l.price_total ELSE 0 END), 0
                    ) AS price_total,
                    COALESCE(t.name->>'en_US', t.name->>'en_GB', t.name::text) AS product_name
                FROM
                    product_template t
                LEFT JOIN
                    product_product p ON t.id = p.product_tmpl_id
                LEFT JOIN
                    sale_order_line l ON p.id = l.product_id
                LEFT JOIN
                    sale_order o ON l.order_id = o.id
                {where_sql}
                GROUP BY
                    t.id, t.name
                {having_sql}
            """

        self.env.cr.execute(query, tuple(params))
        return self.env.cr.fetchall()
