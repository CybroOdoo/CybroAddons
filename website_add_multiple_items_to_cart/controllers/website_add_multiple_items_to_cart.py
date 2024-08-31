# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj (odoo@cybrosys.com)
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
# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class WebsiteAddMultiProduct(http.Controller):
    """Controller for adding multiple products to the cart on the website."""
    @http.route('/shop/cart/add_multi_product', type='json', auth="public", methods=['POST'], website=True)
    def cart_add_multi_product(self, **kw):
        """Add selected products to cart"""
        sale_order = request.website.sale_get_order(force_create=True)
        product_ids = kw.get('product_ids', [])
        added_qty = 0
        for product_id in product_ids:
            product_id = int(product_id)
            order_line = sale_order.order_line.filtered(lambda line: line.product_id.id == product_id)
            if order_line:
                order_line.product_uom_qty += 1
            else:
                sale_order._cart_update(
                    product_id=product_id,
                    add_qty=1,
                    set_qty=1,
                )
            added_qty += 1
        request.session['website_sale_cart_quantity'] = sale_order.cart_quantity
        return {'added_qty': added_qty, 'total_qty': sale_order.cart_quantity}

    @http.route(['/shop/cart/qty'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_qty_check(self):
        """Check cart quantity and update the value in session storage"""
        cart_qty = request.website.sale_get_order().cart_quantity
        request.session['website_sale_cart_quantity'] = cart_qty
        return cart_qty
