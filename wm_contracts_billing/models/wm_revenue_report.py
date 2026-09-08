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


class WmRevenueReport(models.Model):
    """Reporting model for Revenue Analysis (_auto = False)."""
    _name = 'wm.revenue.report'
    _description = 'Revenue Analysis Report'
    _auto = False
    _order = 'date desc, id desc'

    waste_category_id = fields.Many2one('wm.waste.category', string='Waste Category', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    date = fields.Date(string='Invoice Date', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Invoice Status', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    invoiced_amount = fields.Float(string='Invoiced Amount', readonly=True)
    weight_kg = fields.Float(string='Weight (kg)', readonly=True)
    revenue_per_kg = fields.Float(string='Revenue per kg', readonly=True)

    def init(self):
        """
        Initialise the wm_revenue_report SQL view by dropping and re-creating
        the materialised view from the underlying collection order and invoice
        line join query.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wm_revenue_report AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    COALESCE(l.category_id, pt.wm_waste_category_id) AS waste_category_id,
                    o.partner_id AS partner_id,
                    CAST(COALESCE(m.invoice_date, m.date, o.scheduled_start, o.create_date) AS DATE) AS date,
                    COALESCE(m.state, 'draft') AS state,
                    o.company_id AS company_id,
                    SUM(COALESCE(l.total_amount, l.price * l.weight, 0.0)) AS invoiced_amount,
                    SUM(COALESCE(l.weight, 0.0)) AS weight_kg,
                    CASE
                        WHEN SUM(COALESCE(l.weight, 0.0)) > 0 THEN
                            SUM(COALESCE(l.total_amount, l.price * l.weight, 0.0)) / SUM(COALESCE(l.weight, 0.0))
                        ELSE 0.0
                    END AS revenue_per_kg
                FROM wm_collection_order_line l
                JOIN wm_collection_order o ON l.order_id = o.id
                LEFT JOIN wm_consolidated_invoice ci ON o.consolidated_invoice_id = ci.id
                LEFT JOIN account_move m ON ci.invoice_id = m.id
                LEFT JOIN product_product p ON l.product_id = p.id
                LEFT JOIN product_template pt ON p.product_tmpl_id = pt.id
                GROUP BY
                    COALESCE(l.category_id, pt.wm_waste_category_id),
                    o.partner_id,
                    CAST(COALESCE(m.invoice_date, m.date, o.scheduled_start, o.create_date) AS DATE),
                    COALESCE(m.state, 'draft'),
                    o.company_id
            )
        """)
