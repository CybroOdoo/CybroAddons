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
from odoo import fields, models


class WmRecyclingEfficiencyReport(models.Model):
    """Reporting model for Recycling Efficiency (_auto = False)."""
    _name = 'wm.recycling.efficiency.report'
    _description = 'Recycling Efficiency Report'
    _auto = False
    _order = 'date desc, source_product_id'

    source_product_id = fields.Many2one('product.product', string='Waste Material (Input)', readonly=True)
    recovered_product_id = fields.Many2one('product.product', string='Recovered Product', readonly=True)
    category_id = fields.Many2one('wm.waste.category', string='Waste Category', readonly=True)
    date = fields.Date(string='Completion Date', readonly=True)
    facility_location_id = fields.Many2one('stock.location', string='Facility Location', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    input_qty = fields.Float(string='Input Qty', readonly=True)
    target_qty = fields.Float(string='Target Qty', readonly=True)
    actual_qty = fields.Float(string='Actual Qty', readonly=True)
    efficiency_pct = fields.Float(string='Efficiency (%)', readonly=True, aggregator='avg')
    co2_avoided_tons = fields.Float(string='Carbon Abated (tCO2e)', readonly=True)

    def init(self):
        """
        Create or replace the SQL view for recycling efficiency analysis.
        """
        self.env.cr.execute("""
            DROP VIEW IF EXISTS wm_recycling_efficiency_report;
            CREATE OR REPLACE VIEW wm_recycling_efficiency_report AS (
                SELECT
                    l.id AS id,
                    o.product_id AS source_product_id,
                    l.product_id AS recovered_product_id,
                    o.category_id AS category_id,
                    o.date_done AS date,
                    o.facility_location_id AS facility_location_id,
                    o.company_id AS company_id,

                    -- To avoid duplicating the total input quantity in aggregations across multiple lines,
                    -- we split the order's input_qty evenly across its recovery lines.
                    COALESCE(o.input_qty, 0.0) / NULLIF(
                        (SELECT count(*) FROM recycling_line WHERE order_id = o.id), 0
                    ) AS input_qty,

                    COALESCE(l.expected_qty, 0.0) AS target_qty,
                    COALESCE(l.recovered_qty, 0.0) AS actual_qty,

                    CASE
                        WHEN l.expected_qty > 0 THEN (l.recovered_qty / l.expected_qty) * 100.0
                        ELSE 0.0
                    END AS efficiency_pct,

                    COALESCE((l.recovered_qty / 1000.0) * COALESCE(c.warm_factor_co2, 1.50), 0.0) AS co2_avoided_tons

                FROM recycling_line l
                JOIN recycling_order o ON l.order_id = o.id
                LEFT JOIN wm_waste_category c ON o.category_id = c.id
                WHERE o.state = 'done'
            )
        """)
