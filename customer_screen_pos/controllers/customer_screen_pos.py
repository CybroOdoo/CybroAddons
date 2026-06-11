# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

    @http.route('/customer/review', type='http', auth="none", website=False, csrf=False)
    def customer_review(self):
        raw_data = request.httprequest.data
        data = json.loads(raw_data.decode('utf-8'))

        if isinstance(data, list):
            data = data[0]

        review_text = data.get("review_text")
        review_star = data.get("review_star")
        session = data.get("session")
        partner_id = data.get("partner_id")
        order_name = data.get("order_name")

        review_model = request.env['pos.order.review'].sudo()
        existing_review = review_model.search([
            ('pos_order_ref', '=', order_name)
        ], limit=1)

        review_vals = {
            'review_text': review_text,
            'review_star': review_star,
            'pos_session': session,
            'partner': partner_id,
            'pos_order_ref': order_name,
        }

        if existing_review:
            existing_review.write(review_vals)
        else:
            review_model.create(review_vals)

        order = request.env['pos.order'].sudo().search([
            ('name', '=', order_name)
        ], limit=1)

        if order:
            rating = {
                "star1": "1",
                "star2": "2",
                "star3": "3",
                "star4": "4",
                "star5": "5",
            }.get(review_star, "0")

            order.write({
                'rating': rating,
                'rating_text': review_text or '',
            })

        return request.make_response(
            json.dumps({'success': True}),
            headers=[('Content-Type', 'application/json')]
        )