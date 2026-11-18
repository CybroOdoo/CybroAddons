# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models

from .dashboard_utils import OUT_OF_STOCK_LIMIT, check_dashboard_access


class StockQuant(models.Model):
    """ Extends 'stock.quant' for retrieving data of products that are out of
    stock."""
    _inherit = "stock.quant"

    @api.model
    def get_out_of_stock(self):
        """ Returns the storable products whose on-hand quantity is lower than
        or equal to the threshold set in the settings, including products that
        never had any stock. Returns None when the graph is disabled."""
        check_dashboard_access(self.env)
        params = self.env['ir.config_parameter'].sudo()
        sett_out_stock_bool = params.get_str(
            "inventory_stock_dashboard_odoo.out_of_stock", default="")
        sett_out_stock_quantity = params.get_str(
            "inventory_stock_dashboard_odoo.out_of_stock_quantity",
            default="")
        if sett_out_stock_bool != "True" or not sett_out_stock_quantity:
            return None
        self.env.flush_all()
        # The quantities are summed per product before the threshold is
        # applied, so a product that is short in one location but available in
        # another one is not reported.
        self.env.cr.execute(
            """SELECT product_product.id AS product_id,
                    COALESCE(SUM(stock_quant.quantity), 0) AS total_qty
                FROM product_product
                INNER JOIN product_template
                    ON product_template.id = product_product.product_tmpl_id
                LEFT JOIN stock_quant
                    ON stock_quant.product_id = product_product.id
                    AND stock_quant.company_id = %(company)s
                    AND stock_quant.location_id IN (
                        SELECT id FROM stock_location
                        WHERE usage = 'internal')
                WHERE product_product.active
                    AND product_template.is_storable
                    AND (product_template.company_id IS NULL
                         OR product_template.company_id = %(company)s)
                GROUP BY product_product.id
                HAVING COALESCE(SUM(stock_quant.quantity), 0) <= %(threshold)s
                ORDER BY total_qty, product_product.id
                LIMIT %(limit)s""",
            {
                'company': self.env.company.id,
                'threshold': int(sett_out_stock_quantity),
                'limit': OUT_OF_STOCK_LIMIT,
            })
        result = self.env.cr.dictfetchall()
        products = self.env['product.product'].sudo().browse(
            [record['product_id'] for record in result])
        names = {product.id: product.display_name for product in products}
        return {
            'product_name': [names[record['product_id']]
                             for record in result],
            'total_quantity': [float(record['total_qty'])
                               for record in result],
        }
