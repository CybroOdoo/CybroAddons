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
from odoo.tools import SQL


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

    def _read_group_select(self, aggregate_spec, query):
        """
        Grouped diversion must be weighted by intake: a plain average of the
        per-line shares is wrong (lines of one order are fractions that should
        add up, orders of different sizes weigh the same). Aggregate it as
        total recycled / total intake instead.
        """
        if aggregate_spec == 'landfill_diversion_pct:avg':
            return SQL(
                'COALESCE(SUM(%(recycled)s) / NULLIF(SUM(%(intake)s), 0.0) * 100.0, 0.0)',
                recycled=self._field_to_sql(self._table, 'recycled_qty_kg', query),
                intake=self._field_to_sql(self._table, 'input_qty_kg', query),
            )
        return super()._read_group_select(aggregate_spec, query)

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

                    -- Quantities are expressed in kg whenever the unit is
                    -- convertible to kilograms (raw quantity otherwise).
                    COALESCE(o.input_qty, 0.0) * CASE
                        WHEN iu.id IS NOT NULL AND kg.id IS NOT NULL
                             AND split_part(iu.parent_path, '/', 1) = split_part(kg.parent_path, '/', 1)
                        THEN iu.factor / kg.factor ELSE 1.0 END / NULLIF(
                        (SELECT count(*) FROM recycling_line WHERE order_id = o.id), 0
                    ) AS input_qty_kg,

                    COALESCE(l.recovered_qty, 0.0) * CASE
                        WHEN lu.id IS NOT NULL AND kg.id IS NOT NULL
                             AND split_part(lu.parent_path, '/', 1) = split_part(kg.parent_path, '/', 1)
                        THEN lu.factor / kg.factor ELSE 1.0 END AS recycled_qty_kg,
                    COALESCE(c.warm_factor_co2, 1.50) AS warm_factor_co2,

                    COALESCE((l.recovered_qty * CASE
                        WHEN lu.id IS NOT NULL AND kg.id IS NOT NULL
                             AND split_part(lu.parent_path, '/', 1) = split_part(kg.parent_path, '/', 1)
                        THEN lu.factor / kg.factor ELSE 1.0 END / 1000.0)
                        * COALESCE(c.warm_factor_co2, 1.50), 0.0) AS co2_avoided_tons,

                    -- Share of the order input recovered by this line, both
                    -- sides in the batch unit.
                    CASE
                        WHEN o.input_qty > 0 THEN (l.recovered_qty * CASE
                            WHEN lu.id IS NOT NULL AND iu.id IS NOT NULL
                                 AND split_part(lu.parent_path, '/', 1) = split_part(iu.parent_path, '/', 1)
                            THEN lu.factor / iu.factor ELSE 1.0 END / o.input_qty) * 100.0
                        ELSE 0.0
                    END AS landfill_diversion_pct

                FROM recycling_line l
                JOIN recycling_order o ON l.order_id = o.id
                LEFT JOIN wm_waste_category c ON o.category_id = c.id
                LEFT JOIN uom_uom lu ON lu.id = l.uom_id
                LEFT JOIN uom_uom iu ON iu.id = o.input_uom_id
                LEFT JOIN ir_model_data kgd ON kgd.module = 'uom' AND kgd.name = 'product_uom_kgm'
                LEFT JOIN uom_uom kg ON kg.id = kgd.res_id
                WHERE o.state in ('in_progress', 'done')
            )
        """)
