# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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


class ProductPivotReport(models.Model):
    """ Model for generating pivot view based on product locations"""
    _name = 'stock.location.product'
    _description = "Product Location Report"
    _auto = False

    product_id = fields.Many2one('product.template', string="Product",
                                 help='Name of the product')
    location_id = fields.Many2one('stock.location', string='Location',
                                  help='Choose the location')
    on_hand_qty = fields.Integer(string='On Hand Quantity',
                                 help='On hand quantity of the product')
    qty_incoming = fields.Integer(string='Incoming Quantity',
                                  help='Incoming quantity of the product')
    qty_outgoing = fields.Integer(string='Outgoing Quantity',
                                  help='Outgoing quantity of the product')
    forecast_qty = fields.Integer(string='Forecast Quantity',
                                  help='Forecasted quantity of the product')

    def init(self):
        """Initialize the view. Drops the existing view if it exists and
        creates a new view with the following columns for the Product model"""
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(''' CREATE OR REPLACE VIEW %s AS (
        SELECT row_number() OVER () AS id,
        product_template.id AS product_id,
        stock_location.id AS location_id,
        SUM(stock_quant.quantity) AS on_hand_qty,
        SUM(stock_quant.quantity + 
         product_template.qty_incoming - product_template.qty_outgoing)
         AS forecast_qty,
        SUM(product_template.qty_incoming) AS qty_incoming,
        SUM(product_template.qty_outgoing) AS qty_outgoing
        FROM product_template
        INNER JOIN product_product ON 
        product_product.product_tmpl_id = product_template.id
        INNER JOIN stock_quant ON stock_quant.product_id = product_product.id
        INNER JOIN stock_location ON
         stock_quant.location_id = stock_location.id
        WHERE stock_location.usage = 'internal'
        GROUP BY product_template.id, stock_location.id)''' % (self._table,))
