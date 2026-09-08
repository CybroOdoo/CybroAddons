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


class WmCustomerProfitabilityReport(models.Model):
    """Reporting model for Customer Profitability and Overage (_auto = False)."""
    _name = 'wm.customer.profitability.report'
    _description = 'Customer Profitability & Overage Report'
    _auto = False
    _order = 'date desc, id desc'

    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    contract_id = fields.Many2one('wm.partner.contract', string='Contract', readonly=True)
    billing_basis = fields.Selection([
        ('per_collection', 'Per Collection'),
        ('material', 'Per Material'),
        ('hybrid', 'Base Fee + Material Overage'),
        ('category_rate', 'Per Category Rate'),
    ], string='Billing Basis', readonly=True)
    date = fields.Date(string='Collection Date', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    total_orders = fields.Integer(string='Total Orders', readonly=True)
    total_weight_kg = fields.Float(string='Total Weight (kg)', readonly=True)
    overage_weight_kg = fields.Float(string='Overage Weight (kg)', readonly=True)
    revenue = fields.Monetary(string='Revenue', currency_field='currency_id', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)

    def init(self):
        """
        Create or replace the SQL view for profitability analysis.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("SELECT 1 FROM information_schema.tables WHERE table_name='wm_consolidated_invoice'")
        if not self.env.cr.fetchone():
            self.env.cr.execute(f"CREATE OR REPLACE VIEW {self._table} AS (SELECT 1 AS id, NULL::integer AS partner_id, NULL::integer AS contract_id, NULL::varchar AS billing_basis, NULL::date AS date, NULL::integer AS company_id, NULL::integer AS currency_id, 0 AS total_orders, 0.0::numeric AS total_weight_kg, 0.0::numeric AS overage_weight_kg, 0.0::numeric AS revenue WHERE False)")
            return
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wm_customer_profitability_report AS (
                SELECT
                    o.id AS id,
                    o.partner_id AS partner_id,
                    o.contract_id AS contract_id,
                    c.billing_basis AS billing_basis,
                    CAST(COALESCE(o.actual_end, o.scheduled_start, o.create_date) AS DATE) AS date,
                    o.company_id AS company_id,
                    c.currency_id AS currency_id,
                    1 AS total_orders,
                    COALESCE(o.confirmed_weight, 0.0) AS total_weight_kg,
                    CASE
                        WHEN c.billing_basis = 'per_collection' AND COALESCE(c.max_weight, 0.0) > 0 THEN GREATEST(0.0, COALESCE(o.confirmed_weight, 0.0) - c.max_weight)
                        WHEN c.billing_basis = 'hybrid' AND COALESCE(c.included_weight, 0.0) > 0 THEN GREATEST(0.0, COALESCE(o.confirmed_weight, 0.0) - c.included_weight)
                        ELSE 0.0
                    END AS overage_weight_kg,
                    COALESCE((SELECT SUM(COALESCE(l.total_amount, l.price * l.weight, 0.0)) FROM wm_collection_order_line l WHERE l.order_id = o.id), 0.0) AS revenue
                FROM wm_collection_order o
                JOIN wm_partner_contract c ON o.contract_id = c.id
                WHERE o.state IN ('completed', 'signed')
            )
        """)
