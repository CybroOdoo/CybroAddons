# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Athira PS (odoo@cybrosys.com)
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
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class ProductAddToCart(WebsiteSale):
    """Class for add to cart."""

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
        """Perform a shopping operation.
           Args:
               page (int): The page number of the shop.
               category (str): The category of products to filter.
               search (str): The search keyword to filter products.
               min_price (float): The minimum price of products to filter.
               max_price (float): The maximum price of products to filter.
               ppg (bool): Whether to paginate the results.
               **post: Additional keyword arguments.
           Returns:
               A response object with updated context.
           """
        response = super(ProductAddToCart, self).shop(page, category, search,
                                                      min_price, max_price, ppg,
                                                      **post)
        response.qcontext.update(
            val=request.env['sale.order.template'].sudo().search([]))
        return response

    @http.route('/product/add_cart', type='http', auth="public",
                methods=['POST'], website=True, csrf=False)
    def cart_update_product(self, express=False, add_qty=1, set_qty=0,
                            product_custom_attribute_values=None,
                            no_variant_attribute_values=None, **kw):
        """Add products inside the quotation template into cart"""
        order_temp = request.env['sale.order.template'].sudo().browse(
            int(kw.get('prod_id')))
        sale_order = request.website.sale_get_order(force_create=True)
        for products in order_temp.sale_order_template_line_ids:
            sale_order._cart_update(
                product_id=int(products.product_id),
                add_qty=products.product_uom_qty,
                set_qty=set_qty,
                product_custom_attribute_values=product_custom_attribute_values,
                no_variant_attribute_values=no_variant_attribute_values, **kw)
            request.session[
                'website_sale_cart_quantity'] = sale_order.cart_quantity
        if express:
            return request.redirect("/shop/checkout?express=1")
        return request.redirect("/shop/cart")
