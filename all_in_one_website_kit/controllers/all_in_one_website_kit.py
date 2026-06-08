# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions (odoo@cybrosys.com)
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
################################################################################
import time
from odoo import http
from odoo.http import request


class WebsiteClearCart(http.Controller):
    """
    The class WebsiteClearCart is used to clear the cart.
        Methods:
            remove_cart_items(self):
            It will remove all items from cart and redirect to shop page
    """

    @http.route(['/shop/remove_items'], type="http", auth="public",
                website=True)
    def remove_cart_items(self):
        """It will remove all items from cart and redirect to shop page"""
        if request.cart:
            request.cart.order_line.unlink()
            request.session['website_sale_cart_quantity'] = 0
        return request.redirect('/shop/cart')

    @http.route('/final/customer_rating', type='http', auth="public",
                website=True, sitemap=False)
    def customer_order_rating(self, **kw):
        """ This function helps to fetch the values of comment and rating """
        order_id_raw = kw.get('order_id', '')
        if not order_id_raw or not str(order_id_raw).strip().isdigit():
            return request.redirect('/shop')
        order_id = request.env['sale.order'].sudo().browse(int(order_id_raw))
        order_id.comment = kw.get('comment', '')
        order_id.rating = kw.get('rate_value', 0)
        return request.redirect('/shop/confirmation')

    @http.route('/get_dashboard_carousel', auth="public", type='jsonrpc')
    def get_dashboard_carousel(self):
        """Getting data to the carousel"""
        events_per_slide = 3
        records = request.env['insta.post'].sudo().search([])
        records_grouped = [records[post:post + events_per_slide] for post in
                           range(0, len(records), events_per_slide)]
        values = {
            "objects": records_grouped,
            "events_per_slide": events_per_slide,
            "num_slides": len(records_grouped),
            "uniqueId": "pc-%d" % int(time.time() * 1000),
        }
        response = http.Response(
            template='all_in_one_website_kit.s_carousel_template_items',
            qcontext=values)
        return response.render()


from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController

class WebsiteSaleVariantControllerInherit(WebsiteSaleVariantController):
    @http.route()
    def get_combination_info_website(self, product_template_id, product_id, combination, add_qty, uom_id=None, **kwargs):
        """Method to get combination info website"""
        res = super(WebsiteSaleVariantControllerInherit, self).get_combination_info_website(
            product_template_id, product_id, combination, add_qty, uom_id, **kwargs
        )
        if res.get('product_id'):
            product = request.env['product.product'].sudo().browse(res['product_id'])
            res['website_hide_variants'] = product.website_hide_variants
        return res
