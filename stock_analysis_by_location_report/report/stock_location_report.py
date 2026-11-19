# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo import api, models
from odoo.tools import groupby


class StockLocationReport(models.AbstractModel):
    """Prepare stock-by-location values for PDF and XLSX reports."""
    _name = "report.stock_analysis_by_location_report.report_stock_location"
    _description = "Stock Analysis By Location Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        report_type = data.get('report_type', 'product')
        product_id = data.get('product_id') or False
        product_variant_id = data.get('product_variant_id') or False
        values = self.query_data(report_type, product_id, product_variant_id)
        grouped_data = {}
        for product_name, rows in groupby(
                values, key=lambda row: row['product']):
            grouped_data[product_name] = list(rows)
        return {'grouped_data': grouped_data, 'var': values}

    @api.model
    def query_data(self, report_type, product_id=False,
                   product_variant_id=False, from_date=False, to_date=False):
        """Return quantities grouped by product and internal stock location."""
        if report_type not in ('product', 'product_variant'):
            raise ValueError("Unsupported stock report type.")

        if report_type == 'product':
            product_join = "pp.product_tmpl_id = pt.id"
            product_filter = "AND pt.id = %(product_id)s" if product_id else ""
            incoming_group = "pp_inner.product_tmpl_id"
            incoming_join = "incoming.product_id = pt.id"
            outgoing_group = "pp_inner.product_tmpl_id"
            outgoing_join = "outgoing.product_id = pt.id"
            group_product = "pt.id, pt.name"
            entity_id_select = "pt.id AS entity_id"
        else:
            product_join = "pp.product_tmpl_id = pt.id"
            product_filter = "AND pp.id = %(product_variant_id)s" if product_variant_id else ""
            incoming_group = "sm.product_id"
            incoming_join = "incoming.product_id = pp.id"
            outgoing_group = "sm.product_id"
            outgoing_join = "outgoing.product_id = pp.id"
            group_product = "pp.id, pt.id, pt.name"
            entity_id_select = "pp.id AS entity_id"

        # Odoo 19 stores translated product names as JSONB.
        query = f"""
            SELECT
                row_number() OVER (ORDER BY pt.id, sl.id) AS id,
                {entity_id_select},
                COALESCE(pt.name->>'en_US', pt.name::text) AS product,
                sl.complete_name AS location,
                COALESCE(SUM(sq.quantity), 0.0) AS on_hand_qty,
                COALESCE(incoming.qty_incoming, 0.0) AS qty_incoming,
                COALESCE(outgoing.qty_outgoing, 0.0) AS qty_outgoing,
                COALESCE(SUM(sq.quantity), 0.0)
                    + COALESCE(incoming.qty_incoming, 0.0)
                    - COALESCE(outgoing.qty_outgoing, 0.0) AS forecast_qty
            FROM stock_quant sq
            JOIN product_product pp ON pp.id = sq.product_id
            JOIN product_template pt ON {product_join}
            JOIN stock_location sl ON sl.id = sq.location_id
            LEFT JOIN (
                SELECT {incoming_group} AS product_id,
                       sm.location_dest_id AS location_id,
                       SUM(sm.product_uom_qty) AS qty_incoming
                FROM stock_move sm
                JOIN product_product pp_inner ON pp_inner.id = sm.product_id
                JOIN stock_location dest ON dest.id = sm.location_dest_id
                WHERE sm.state NOT IN ('cancel', 'done')
                  AND dest.usage = 'internal'
                GROUP BY {incoming_group}, sm.location_dest_id
            ) incoming ON {incoming_join} AND incoming.location_id = sl.id
            LEFT JOIN (
                SELECT {outgoing_group} AS product_id,
                       sm.location_id AS location_id,
                       SUM(sm.product_uom_qty) AS qty_outgoing
                FROM stock_move sm
                JOIN product_product pp_inner ON pp_inner.id = sm.product_id
                JOIN stock_location src ON src.id = sm.location_id
                WHERE sm.state NOT IN ('cancel', 'done')
                  AND src.usage = 'internal'
                GROUP BY {outgoing_group}, sm.location_id
            ) outgoing ON {outgoing_join} AND outgoing.location_id = sl.id
            WHERE sl.usage = 'internal'
              {product_filter}
            GROUP BY {group_product}, sl.id, sl.complete_name,
                     incoming.qty_incoming, outgoing.qty_outgoing
            ORDER BY product, location
        """
        params = {
            'product_id': product_id,
            'product_variant_id': product_variant_id,
        }
        self.env.cr.execute(query, params)
        rows = self.env.cr.dictfetchall()
        if report_type == 'product_variant':
            variant_ids = [r['entity_id'] for r in rows if r.get('entity_id')]
            if variant_ids:
                variant_names = {
                    v.id: v.display_name
                    for v in self.env['product.product'].browse(variant_ids)
                }
                for r in rows:
                    if r.get('entity_id') in variant_names:
                        r['product'] = variant_names[r['entity_id']]
        else:
            template_ids = [r['entity_id'] for r in rows if r.get('entity_id')]
            if template_ids:
                template_names = {
                    t.id: t.display_name
                    for t in self.env['product.template'].browse(template_ids)
                }
                for r in rows:
                    if r.get('entity_id') in template_names:
                        r['product'] = template_names[r['entity_id']]
        return rows
