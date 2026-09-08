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


class WmCarbonAccountingReport(models.Model):
    """SQL view for ESG Scope 3 carbon accounting, measuring CO₂ abatement from recovered materials."""
    _name = 'wm.carbon.accounting.report'
    _description = 'ESG & Carbon Accounting Report'
    _auto = False
    _order = 'date desc, category_id'

    date = fields.Date(string='Date', readonly=True)
    category_id = fields.Many2one('wm.waste.category', string='Waste Category', readonly=True)
    source_product_id = fields.Many2one('product.product', string='Waste Material', readonly=True)
    facility_location_id = fields.Many2one('stock.location', string='Facility Location', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    input_qty_kg = fields.Float(string='Raw Waste Intake (kg)', readonly=True)
    recycled_qty_kg = fields.Float(string='Recycled Material (kg)', readonly=True)
    warm_factor_co2 = fields.Float(string='EPA WARM Factor (tCO2e/MT)', readonly=True, aggregator='avg')
    co2_avoided_tons = fields.Float(string='Carbon Abated (tCO2e)', readonly=True)
    landfill_diversion_pct = fields.Float(string='Landfill Diversion (%)', readonly=True, aggregator='avg')

    def init(self):
        """
        Create or replace the SQL view for ESG & Carbon Accounting.
        """
        self.env.cr.execute("""
            DROP VIEW IF EXISTS wm_carbon_accounting_report;
            CREATE OR REPLACE VIEW wm_carbon_accounting_report AS (
                SELECT
                    l.id AS id,
                    COALESCE(o.date_done, o.date_start) AS date,
                    o.category_id AS category_id,
                    o.product_id AS source_product_id,
                    o.facility_location_id AS facility_location_id,
                    o.company_id AS company_id,

                    COALESCE(o.input_qty, 0.0) / NULLIF(
                        (SELECT count(*) FROM recycling_line WHERE order_id = o.id), 0
                    ) AS input_qty_kg,

                    COALESCE(l.recovered_qty, 0.0) AS recycled_qty_kg,
                    COALESCE(c.warm_factor_co2, 1.50) AS warm_factor_co2,

                    COALESCE((l.recovered_qty / 1000.0) * COALESCE(c.warm_factor_co2, 1.50), 0.0) AS co2_avoided_tons,

                    CASE
                        WHEN o.input_qty > 0 THEN (l.recovered_qty / o.input_qty) * 100.0
                        ELSE 0.0
                    END AS landfill_diversion_pct

                FROM recycling_line l
                JOIN recycling_order o ON l.order_id = o.id
                LEFT JOIN wm_waste_category c ON o.category_id = c.id
                WHERE o.state in ('in_progress', 'done')
            )
        """)
