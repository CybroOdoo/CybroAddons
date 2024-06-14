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
    """ Model for generating pivot view for product variants based on product
     locations"""
    _name = 'stock.location.product.variant'
    _description = "Product Variant Location Report"
    _auto = False

    product_id = fields.Many2one('product.product', string="Product",
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
        creates a new view with the following columns for the Product variant
        model"""
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(''' CREATE OR REPLACE VIEW %s AS (
        select row_number() OVER () as id, 
        stock_quant.product_id, 
        stock_quant.location_id, 
        stock_quant.quantity on_hand_qty, 
        (stock_quant.quantity + 
         product_product.qty_incoming - product_product.qty_outgoing) 
         AS forecast_qty, 
        product_product.qty_incoming,
        product_product.qty_outgoing from product_product 
        inner JOIN stock_quant on stock_quant.product_id = product_product.id
        inner join product_template on 
        product_product.product_tmpl_id = product_template.id
        inner join stock_location on 
        stock_quant.location_id = stock_location.id
        where stock_location.usage = 'internal')''' % (self._table,))
