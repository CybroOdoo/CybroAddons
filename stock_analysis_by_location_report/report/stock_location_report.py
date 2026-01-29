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
from odoo import api, models
from odoo.tools import groupby


class StockLocationReport(models.AbstractModel):
    """To generate report based on query and get report values"""
    _name = "report.stock_analysis_by_location_report.report_stock_location"

    @api.model
    def _get_report_values(self, docids, data=None):
        """ To get the report values based on the user giving conditions """
        value = self.query_data(data['report_type'], data['product_id'],
                                data['product_variant_id'])
        grouped_data = {}
        for product_id, group in (
                groupby(value, key=lambda x: x['product'])):
            grouped_data[product_id] = list(group)
        return {
            'grouped_data': grouped_data,
            'var': value
        }

    def query_data(self, report_type, product_id, product_variant_id):
        """ To fetch values from database using query """
        if report_type == 'product':
            query = """SELECT row_number() OVER () AS id,
            product_template.name AS product,
            stock_location.complete_name AS location,
            SUM(stock_quant.quantity) AS on_hand_qty,
            SUM(stock_quant.quantity + 
             product_template.qty_incoming - product_template.qty_outgoing) 
             AS forecast_qty,
            SUM(product_template.qty_incoming) AS qty_incoming,
            SUM(product_template.qty_outgoing) AS qty_outgoing
            FROM product_template 
            INNER JOIN product_product ON 
             product_product.product_tmpl_id = product_template.id
            INNER JOIN stock_quant ON 
             stock_quant.product_id = product_product.id
            INNER JOIN stock_location ON
             stock_quant.location_id = stock_location.id
            WHERE stock_location.usage = 'internal'
            GROUP BY product_template.id, stock_location.id"""
            if product_id:
                query = """SELECT row_number() OVER () AS id,
                product_template.name AS product,
                stock_location.complete_name AS location,
                SUM(stock_quant.quantity) AS on_hand_qty,
                SUM(stock_quant.quantity +
                 product_template.qty_incoming - product_template.qty_outgoing)
                 AS forecast_qty,
                SUM(product_template.qty_incoming) AS qty_incoming,
                SUM(product_template.qty_outgoing) AS qty_outgoing
                FROM product_template 
                INNER JOIN product_product ON
                 product_product.product_tmpl_id = product_template.id
                INNER JOIN stock_quant ON
                 stock_quant.product_id = product_product.id
                INNER JOIN stock_location ON
                 stock_quant.location_id = stock_location.id
                WHERE stock_location.usage = 'internal' 
                and product_template.id=%(product_id)s
                GROUP BY product_template.id, stock_location.id"""
        else:
            query = """select product_template.name as Product,
            stock_location.complete_name as Location,
            stock_quant.quantity on_hand_qty, 
            (stock_quant.quantity + 
            product_product.qty_incoming - product_product.qty_outgoing)  
             AS forecast_qty,  product_product.qty_incoming,
            product_product.qty_outgoing from product_product 
            inner JOIN stock_quant on 
             stock_quant.product_id = product_product.id 
            inner join product_template 
             on product_product.product_tmpl_id = product_template.id
            inner join stock_location on
             stock_quant.location_id = stock_location.id
            where stock_location.usage = 'internal'"""
            if product_variant_id:
                query += """ and product_id=%(product_variant_id)s"""
        self.env.cr.execute(query,
                            {'report_type': report_type,
                             'product_id': product_id,
                             'product_variant_id': product_variant_id,
                             })
        return self.env.cr.dictfetchall()
