# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Henna Mehjabin (odoo@cybrosys.com)
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
from odoo import http
from odoo.http import request


class WebsiteAddMultiProduct(http.Controller):
    """Controller for adding multiple products to the cart on the website."""

    @http.route('/shop/cart/add_multi_product', type='json', auth="public",
                methods=['POST'], website=True)
    def cart_add_multi_product(self, **kw):
        """Add selected products to cart"""
        sale_order = request.cart or request.website._create_cart()

        product_ids = kw.get('product_ids', [])

        added_qty = 0
        failed_products = []

        for product_id in product_ids:
            try:
                product_id = int(product_id)

                product = request.env['product.product'].browse(product_id).exists()

                if not product or not product._is_add_to_cart_allowed():
                    failed_products.append(product_id)
                    continue

                order_line = sale_order.order_line.filtered(
                    lambda line: line.product_id.id == product_id
                )
                if order_line:
                    sale_order._cart_update_line_quantity(
                        line_id=order_line[0].id,
                        quantity=order_line[0].product_uom_qty + 1
                    )
                else:
                    values = sale_order.with_context(
                        skip_cart_verification=True
                    )._cart_add(
                        product_id=product_id,
                        quantity=1,
                    )
                    if not values.get('line_id'):
                        failed_products.append(product_id)
                        continue

                added_qty += 1

            except Exception as e:
                failed_products.append(product_id)

        if added_qty > 0:
            sale_order._verify_cart_after_update()

        request.session['website_sale_cart_quantity'] = sale_order.cart_quantity

        return {
            'added_qty': added_qty,
            'total_qty': sale_order.cart_quantity,
            'failed_products': failed_products,
            'cart_ready': sale_order._is_cart_ready() if hasattr(sale_order, '_is_cart_ready') else True
        }

    @http.route(['/shop/cart/qty'], type='json', auth="public",
                methods=['POST'], website=True, csrf=False)
    def cart_qty_check(self):
        """Check cart quantity and update the value in session storage"""
        sale_order = request.cart
        cart_qty = sale_order.cart_quantity if sale_order else 0
        request.session['website_sale_cart_quantity'] = cart_qty
        return cart_qty
