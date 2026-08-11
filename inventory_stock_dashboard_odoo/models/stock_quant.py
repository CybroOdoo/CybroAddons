# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Manasa T P (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, models


class StockQuant(models.Model):
    """ Extends 'stock.quant' for retrieving data of products that are out of
    stock."""
    _inherit = "stock.quant"

    @api.model
    def get_out_of_stock(self):
        """ Returns products and quantities that are out of stock."""
        company_id = self.env.company.id
        sett_out_stock_bool = self.env['ir.config_parameter'].sudo(). \
            get_param("inventory_stock_dashboard_odoo.out_of_stock", default="")
        sett_out_stock_quantity = self.env['ir.config_parameter'].sudo().\
            get_param("inventory_stock_dashboard_odoo.out_of_stock_quantity", default="")
        if sett_out_stock_bool == "True":
            if sett_out_stock_quantity:
                out_stock_value = int(sett_out_stock_quantity)
                query = '''select product_product.id, SUM(stock_quant.quantity) AS total_qty from product_product
                                 inner join stock_quant on product_product.id = stock_quant.product_id
                                 where stock_quant.quantity < %s and stock_quant.company_id = %s group by product_product.id''' \
                       % (out_stock_value, company_id)
                self.env.cr.execute(query)
                result = self.env.cr.dictfetchall()
                total_quantity = []
                product_name = []
                for record in result:
                    qty = record.get('total_qty', 0)
                    if qty <= out_stock_value: # Show negative or zero quantity products
                        total_quantity.append(qty)
                        complete_name = self.env['product.product'].browse(
                            record['id']).display_name
                        product_name.append(complete_name)

                value = {
                    'product_name': product_name,
                    'total_quantity': total_quantity
                }
                return value
