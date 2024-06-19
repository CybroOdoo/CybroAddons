# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
        current_orders = request.website.sale_get_order()
        for line in current_orders.website_order_line:
            line.unlink()
        return request.redirect('/shop/cart')

    @http.route('/final/customer_rating', type='http', auth="public",
                website=True, sitemap=False)
    def customer_order_rating(self, **kw):
        """ This function helps to fetch the values of comment and rating """
        order_id = request.env['sale.order'].sudo().browse(int(kw['order_id']))
        order_id.comment = kw['comment']
        order_id.rating = kw['rate_value']
        return request.redirect('/shop/confirmation')

    @http.route('/get_dashboard_carousel', auth="public", type='json')
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
