# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models
from odoo.tools.sql import SQL



class PurchaseReport(models.Model):
    """Inherit model to add fields and methods"""
    _inherit = 'purchase.report'

    brand_id = fields.Many2one(
        'product.brand', string='Brand', help='Select brand of the product'
    )

    def _select(self):
        """Add filter in pivot view"""
        query = """
        SELECT 
            po.id AS order_id,
            MIN(l.id) AS id,
            po.date_order AS date_order,
            po.state,
            po.date_approve,
            po.dest_address_id,
            po.partner_id AS partner_id,
            po.user_id AS user_id,
            po.company_id AS company_id,
            po.fiscal_position_id AS fiscal_position_id,
            l.product_id,
            p.product_tmpl_id,
            t.categ_id AS category_id,
            t.brand_id AS brand_id,
            c.currency_id,
            t.uom_id AS product_uom,
            EXTRACT(EPOCH FROM AGE(po.date_approve, po.date_order)) / (24 * 60 * 60)::DECIMAL(16,2) AS delay,
            EXTRACT(EPOCH FROM AGE(l.date_planned, po.date_order)) / (24 * 60 * 60)::DECIMAL(16,2) AS delay_pass,
            COUNT(*) AS nbr_lines,
            SUM(l.price_total / COALESCE(po.currency_rate, 1.0))::DECIMAL(16,2) * account_currency_table.rate AS price_total,
            (SUM(l.product_qty * l.price_unit / COALESCE(po.currency_rate, 1.0)) /
            NULLIF(SUM(l.product_qty / line_uom.factor * product_uom.factor), 0.0))::DECIMAL(16,2) * account_currency_table.rate AS price_average,
            partner.country_id AS country_id,
            partner.commercial_partner_id AS commercial_partner_id,
            SUM(p.weight * l.product_qty / line_uom.factor * product_uom.factor) AS weight,
            SUM(p.volume * l.product_qty / line_uom.factor * product_uom.factor) AS volume,
            SUM(l.price_subtotal / COALESCE(po.currency_rate, 1.0))::DECIMAL(16,2) * account_currency_table.rate AS untaxed_total,
            SUM(l.product_qty / line_uom.factor * product_uom.factor) AS qty_ordered,
            SUM(l.qty_received / line_uom.factor * product_uom.factor) AS qty_received,
            SUM(l.qty_invoiced / line_uom.factor * product_uom.factor) AS qty_billed,
            CASE 
                WHEN t.purchase_method = 'purchase' THEN 
                    SUM(l.product_qty / line_uom.factor * product_uom.factor) - 
                    SUM(l.qty_invoiced / line_uom.factor * product_uom.factor)
                ELSE 
                    SUM(l.qty_received / line_uom.factor * product_uom.factor) - 
                    SUM(l.qty_invoiced / line_uom.factor * product_uom.factor)
            END AS qty_to_be_billed

        """
        updated_res = SQL(query)
        return updated_res

    def _group_by(self):
        """Add the group by in pivot view"""
        updated_res = SQL("""
            GROUP BY 
                po.company_id,
                po.user_id,
                po.partner_id,
                line_uom.factor,
                c.currency_id,
                l.price_unit,
                po.date_approve,
                l.date_planned,
                l.product_uom,
                po.dest_address_id,
                po.fiscal_position_id,
                l.product_id,
                p.product_tmpl_id,
                t.categ_id,
                t.brand_id,
                po.date_order,
                po.state,
                line_uom.uom_type,
                line_uom.category_id,
                t.uom_id,
                t.purchase_method,
                line_uom.id,
                product_uom.factor,
                partner.country_id,
                partner.commercial_partner_id,
                po.id,
                account_currency_table.rate
        """)

        return updated_res
