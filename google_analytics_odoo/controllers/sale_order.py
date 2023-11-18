# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request


class SalesDetails(http.Controller):
    """This class It contains
                  functions for getting the sale order details.
                  Methods:
                      get_order_details():
                          Returns the Sale order details when confirming the
                          purchase order """

    @http.route('/sale_analytics', type="json", auth="public")
    def sales_details(self, **kw):
        """Returns the Sale order details"""
        order = request.env['sale.order'].browse(
            int(kw.get('order_id'))).read()
        product_data = []
        for rec in request.env['sale.order'].browse(
                int(kw.get('order_id'))).mapped('order_line'):
            lines = request.env['sale.order.line'].browse(int(rec))
            product_data.append({
                'product_name': lines.name,
                'price': lines.price_unit,
                'quantity': lines.product_uom_qty,
                'total_price': lines.price_total,
            })
        return {
            'sales_data': {'name': order[0].get('name'),
                           'amount': order[0].get('amount_total'),
                           'customer': order[0].get('partner_id')[1]},
            'product_data': product_data
        }
