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


class WmOperationsReport(models.Model):
    """SQL view for the Operations Overview dashboard, combining collection, recycling, and billing KPIs."""
    _name = 'wm.operations.report'
    _description = 'Operations Overview'
    _auto = False
    _order = 'date desc, id desc'

    waste_category_id = fields.Many2one('wm.waste.category', string='Waste Category', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    collection_point_id = fields.Many2one('wm.collection.point', string='Collection Point', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    weight_kg = fields.Float(string='Weight (kg)', readonly=True)
    volume_l = fields.Float(string='Volume (L)', readonly=True)
    invoiced_amount = fields.Float(string='Invoiced Amount', readonly=True)
    order_count = fields.Integer(string='Order Count', readonly=True)

    def init(self):
        """
        Create or replace SQL view combining operational and financial metrics.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wm_operations_report AS (
                SELECT
                    min(l.id) AS id,
                    pt.wm_waste_category_id AS waste_category_id,
                    o.partner_id AS partner_id,
                    o.collection_point_id AS collection_point_id,
                    CAST(COALESCE(o.scheduled_start, o.completed_date, o.create_date) AS DATE) AS date,
                    o.company_id AS company_id,
                    SUM(COALESCE(l.weight, 0.0)) AS weight_kg,
                    0.0 AS volume_l,
                    SUM(COALESCE(l.total_amount, l.price * l.weight, 0.0)) AS invoiced_amount,
                    COUNT(DISTINCT o.id) AS order_count
                FROM wm_collection_order_line l
                JOIN wm_collection_order o ON l.order_id = o.id
                LEFT JOIN wm_consolidated_invoice ci ON o.consolidated_invoice_id = ci.id
                LEFT JOIN account_move m ON ci.invoice_id = m.id
                LEFT JOIN product_product p ON l.product_id = p.id
                LEFT JOIN product_template pt ON p.product_tmpl_id = pt.id
                WHERE o.state IN ('completed', 'signed')
                GROUP BY
                    pt.wm_waste_category_id,
                    o.partner_id,
                    o.collection_point_id,
                    CAST(COALESCE(o.scheduled_start, o.completed_date, o.create_date) AS DATE),
                    o.company_id
            )
        """)
