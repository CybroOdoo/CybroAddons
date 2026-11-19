# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jigin k(odoo@cybrosys.com)
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
from odoo import fields, models, tools


class StockLocationProductVariant(models.Model):
    """ Model for generating pivot view for product variants based on product
     locations"""
    _name = 'stock.location.product.variant'
    _description = "Product Variant Location Report"
    _auto = False

    product_id = fields.Many2one('product.product', string="Product",
                                 help='Name of the product')
    location_id = fields.Many2one('stock.location', string='Location',
                                  help='Choose the location')
    on_hand_qty = fields.Float(string='On Hand Quantity',
                                 help='On hand quantity of the product')
    qty_incoming = fields.Float(string='Incoming Quantity',
                                  help='Incoming quantity of the product')
    qty_outgoing = fields.Float(string='Outgoing Quantity',
                                  help='Outgoing quantity of the product')
    forecast_qty = fields.Float(string='Forecast Quantity',
                                  help='Forecasted quantity of the product')

    def init(self):
        """Initialize the view. Drops the existing view if it exists and
        creates a new view with the following columns for the Product variant
        model"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(tools.SQL(''' CREATE OR REPLACE VIEW %s AS (
            SELECT
                row_number() OVER () AS id,
                sq.product_id,
                sq.location_id,
                SUM(sq.quantity) AS on_hand_qty,
                COALESCE(incoming.qty_incoming, 0) AS qty_incoming,
                COALESCE(outgoing.qty_outgoing, 0) AS qty_outgoing,
                SUM(sq.quantity)
                    + COALESCE(incoming.qty_incoming, 0)
                    - COALESCE(outgoing.qty_outgoing, 0)
                    AS forecast_qty
            FROM stock_quant sq
            INNER JOIN product_product pp
                ON pp.id = sq.product_id
            INNER JOIN product_template pt
                ON pp.product_tmpl_id = pt.id
            INNER JOIN stock_location sl
                ON sq.location_id = sl.id
            LEFT JOIN (
                SELECT
                    sm.product_id,
                    sm.location_dest_id AS location_id,
                    SUM(sm.product_uom_qty) AS qty_incoming
                FROM stock_move sm
                INNER JOIN stock_location dest
                    ON dest.id = sm.location_dest_id
                WHERE sm.state NOT IN ('cancel', 'done')
                  AND dest.usage = 'internal'
                GROUP BY
                    sm.product_id,
                    sm.location_dest_id
            ) incoming
                ON incoming.product_id = sq.product_id
                AND incoming.location_id = sq.location_id
            LEFT JOIN (
                SELECT
                    sm.product_id,
                    sm.location_id,
                    SUM(sm.product_uom_qty) AS qty_outgoing
                FROM stock_move sm
                INNER JOIN stock_location src
                    ON src.id = sm.location_id
                WHERE sm.state NOT IN ('cancel', 'done')
                  AND src.usage = 'internal'
                GROUP BY
                    sm.product_id,
                    sm.location_id
            ) outgoing
                ON outgoing.product_id = sq.product_id
                AND outgoing.location_id = sq.location_id
            WHERE sl.usage = 'internal'
            GROUP BY
                sq.product_id,
                sq.location_id,
                incoming.qty_incoming,
                outgoing.qty_outgoing
        )''', tools.SQL.identifier(self._table)))
