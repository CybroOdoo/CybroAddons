# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, tools


class WmWeightRevenueReport(models.Model):
    """SQL view mapping collected weights to invoiced revenue for profitability and skip-out analysis."""
    _name = 'wm.weight.revenue.report'
    _description = 'Weight to Revenue Report'
    _auto = False
    _order = 'date desc, id desc'

    order_id = fields.Many2one('wm.collection.order', string='Collection Order', readonly=True)
    waste_category_id = fields.Many2one('wm.waste.category', string='Waste Category', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    date = fields.Date(string='Order Date', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    weight_kg = fields.Float(string='Weight (kg)', readonly=True)
    uninvoiced_amount = fields.Float(string='Uninvoiced Amount', readonly=True)
    uninvoiced_order_count = fields.Integer(string='Uninvoiced Order Count', readonly=True)

    def init(self):
        """
        Create or replace SQL view with LEFT JOIN to surface completed
        uninvoiced orders.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wm_weight_revenue_report AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    o.id AS order_id,
                    COALESCE(l.category_id, pt.wm_waste_category_id) AS waste_category_id,
                    o.partner_id AS partner_id,
                    CAST(COALESCE(o.scheduled_start, o.completed_date, o.create_date) AS DATE) AS date,
                    o.company_id AS company_id,
                    COALESCE(SUM(l.weight), 0.0) AS weight_kg,
                    CASE
                        WHEN o.consolidated_invoice_id IS NULL AND o.billing_run_line_id IS NULL THEN COALESCE(SUM(l.total_amount), 0.0)
                        ELSE 0.0
                    END AS uninvoiced_amount,
                    CASE
                        WHEN o.consolidated_invoice_id IS NULL AND o.billing_run_line_id IS NULL THEN 1
                        ELSE 0
                    END AS uninvoiced_order_count
                FROM wm_collection_order o
                LEFT JOIN wm_collection_order_line l ON l.order_id = o.id
                LEFT JOIN product_product p ON l.product_id = p.id
                LEFT JOIN product_template pt ON p.product_tmpl_id = pt.id
                WHERE o.state IN ('completed', 'signed')
                GROUP BY
                    o.id,
                    COALESCE(l.category_id, pt.wm_waste_category_id),
                    o.partner_id,
                    CAST(COALESCE(o.scheduled_start, o.completed_date, o.create_date) AS DATE),
                    o.company_id,
                    o.consolidated_invoice_id,
                    o.billing_run_line_id
            )
        """)
