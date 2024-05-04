# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (odoo@cybrosys.com)
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
import json
from odoo import http
from odoo.http import request


class AddMyProductReview(http.Controller):
    """ AddMyProductReview class provides the functionality of creating
        templates and model records about customer screen and customer reviews
        Methods:
            add_my_review(self, orderlinelist, total):
                This get the order lines from pos and create a screen template
                and return into pos js fil
            customer_screen_pos(self):
                For create default template for merge customer screen template
            customer_review(self, review):
                For create new records in model "pos.order.review" based on
                customer review that we got from customer screen """
    @http.route('/add/my/review', type='json', auth='public')
    def add_my_review(self, orderlinelist, total):

        """For pass records into order-lines template and return template body
            to js file for generate new page"""
        response = http.Response(
            template='customer_screen_pos.customer_pos_screen',
            qcontext={'orderlinelist': orderlinelist, 'total': total})
        return response.render()

    @http.route(['/customer/screen/'], type='http', auth="user",
                website=True)
    def customer_screen_pos(self):
        """Default customer screen for merge orders list and review template"""
        return (request.render
                ("customer_screen_pos.customer_screen_pos_main_page"))

    @http.route(['/customer/review/<review>'], type='json', auth="none",
                website=False, csrf=False)
    def customer_review(self, review):
        """Get review and rating from customer screen and store into a new
            model based on pos order reference"""
        data = json.loads(review)
        review_text = data[0]["review_text"]
        review_star = data[0]["review_star"]
        pos_order_review = request.env['pos.order.review'].sudo().search([])
        reviews_refer = [review_ref.pos_order_ref for review_ref in
                         pos_order_review]
        if data[0]["order_name"] not in reviews_refer:
            request.env['pos.order.review'].sudo().create({
                'review_text': review_text if review_text else None,
                'review_star': review_star if review_star else None,
                'pos_session': data[0]["session"] if data[0][
                    "session"] else None,
                'partner': data[0]["partner_id"] if data[0][
                    "partner_id"] else None,
                'pos_order_ref': data[0]["order_name"] if data[0][
                    "order_name"] else None,
            })
        else:
            request.env['pos.order.review'].sudo().search(
                [('pos_order_ref', '=', data[0]['order_name'])]).sudo().write({
                    'review_text': review_text if review_text else None,
                    'review_star': review_star if review_star else None,
                    'pos_session': data[0]["session"] if data[0][
                        "session"] else None,
                    'partner': data[0]["partner_id"] if data[0][
                        "partner_id"] else None,
                })
