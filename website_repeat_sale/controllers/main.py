# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#############################################################################

from odoo import http
from odoo.http import request


class WebSaleOrderRepeat(http.Controller):

    @http.route('/order/repeat', type='http', auth="public", website=True)
    def repeat_sale_order(self, **kwargs):
        """Update products to cart when a user clicks reorder button"""
        order_id = kwargs.get('id')
        repeat_order_id = request.env['sale.order'].sudo().browse(
            int(order_id))
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)
        add_qty = 0
        set_qty = 0
        for line1 in repeat_order_id.order_line:
            if line1.product_id:
                if sale_order.order_line:
                    for line2 in sale_order.order_line:
                        if line2.product_id == line1.product_id:
                            add_qty = line1.product_uom_qty + line2.product_uom_qty
                            set_qty = add_qty
                            break
                        else:
                            add_qty = line1.product_uom_qty
                            set_qty = add_qty
                else:
                    add_qty = line1.product_uom_qty
                    set_qty = add_qty

                sale_order._cart_update(
                    product_id=int(line1.product_id.id),
                    add_qty=add_qty,
                    set_qty=set_qty,
                )
        return request.redirect("/shop/cart")

