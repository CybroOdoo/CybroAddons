#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request


class WebsiteAddMultiProduct(http.Controller):
    """Controller for adding multiple products to the cart on the website."""
    @http.route('/shop/cart/add_multi_product', type='http', auth="public",
                methods=['GET'], website=True)
    def cart_add_multi_product(self, **kw):
        """Add selected products to cart"""
        sale_order = request.website.sale_get_order(force_create=True)
        for product_ids in kw.values():
            if product_ids:
                product_id = int(product_ids)
                # Check if the product is already in the cart
                order_line = sale_order.order_line.filtered(
                    lambda line: line.product_id.id == product_id)
                if order_line:
                    # If the product is already in the cart, increase the
                    # quantity by 1
                    order_line.product_uom_qty += 1
                else:
                    # If the product is not in the cart, add it with quantity 1
                    sale_order._cart_update(
                        product_id=product_id,
                        add_qty=1,
                        set_qty=1,
                    )
            request.session['website_sale_cart_quantity'] = (
                sale_order.cart_quantity)

    @http.route(['/shop/cart/qty'], type='json', auth="public",
                methods=['POST'], website=True, csrf=False)
    def cart_qty_check(self):
        """Check cart quantity and update the value in session storage"""
        cart_qty = request.website.sale_get_order().cart_quantity
        request.session['website_sale_cart_quantity'] = cart_qty
        return request.session['website_sale_cart_quantity']
