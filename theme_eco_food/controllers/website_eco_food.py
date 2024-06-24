# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class WebsiteEcoFood(http.Controller):
    """ Class for website to add extra functions"""

    @http.route('/get_best_seller', auth="public", type='json')
    def get_best_seller(self):
        """this function is used to retrieve the best-selling product"""
        products = request.env.ref(
            'theme_eco_food.best_seller_product').product_tmpl_ids.sorted(
            key=lambda x: x.sales_count, reverse=True)[:10]
        best_seller = [{'id': product.id,
                        'name': product.name,
                        'category': product.categ_id.name,
                        'rating_avg': product.rating_avg,
                        'list_price': product.list_price,
                        'currency': product.currency_id.symbol
                        } for product in products]
        return best_seller

    @http.route('/get_featured_products', auth="public", type='json')
    def get_featured_products(self):
        """this function is used to retrieve featured products"""
        products = request.env.ref(
            'theme_eco_food.featured_product').product_tmpl_ids.sorted(
            key=lambda x: x.id, reverse=True)[:8]
        values = {
            f'slide{i + 1}': [{'id': product.id,
                               'name': product.name,
                               'category': product.categ_id.name,
                               'rating_avg': product.rating_avg,
                               'list_price': product.list_price,
                               'currency': product.currency_id.symbol
                               } for product in products[i * 4:(i + 1) * 4]]
            for i in range((len(products) + 3) // 4)
        }
        return values

    @http.route('/get_recently_added_products', auth="public", type='json')
    def get_recently_added_products(self):
        """this function will return the most recently added products."""
        products = request.env.ref(
            'theme_eco_food.recently_added_product').product_tmpl_ids.sorted(
            key=lambda x: x.id, reverse=True)[:16]
        values = {
            f'slide{i + 1}': [{'id': product.id,
                               'name': product.name,
                               'category': product.categ_id.name,
                               'rating_avg': product.rating_avg,
                               'list_price': product.list_price,
                               'currency': product.currency_id.symbol
                               } for product in products[i * 8:(i + 1) * 8]]
            for i in range((len(products) + 7) // 8)
        }
        return values

    @http.route('/get_new_arrivals', auth="public", type='json')
    def get_new_arrivals(self):
        """this function is used to retrieve new arrival products"""
        products = request.env.ref(
            'theme_eco_food.new_arrival_product').product_tmpl_ids.sorted(
            key=lambda x: x.id, reverse=True)[:16]
        values = [{
            'id': product.id,
            'name': product.name,
            'category': product.categ_id.name,
            'rating_avg': product.rating_avg,
            'list_price': product.list_price,
            'currency': product.currency_id.symbol
        } for product in products]
        return values

    @http.route('/get_testimonials', auth="public", type='json')
    def get_testimonials(self):
        """this function is used to retrieve testimonials.py"""
        testimonials = request.env['ecofood.testimonial'].search([]).sorted(
            key=lambda x: x.id, reverse=True)[:16]
        values = {
            f'slide{i + 1}': [{'id': record.id,
                               'name': record.partner_id.name,
                               'email': record.partner_id.email,
                               'review': record.review
                               } for record in testimonials[i * 2:(i + 1) * 2]]
            for i in range((len(testimonials) + 1) // 2)
        }
        return values

    @http.route('/subscribe_newsletter', auth='public', type='json')
    def subscribe_newsletter(self, **kw):
        """ To save email to newsletter mail list"""
        if request.env['mailing.contact'].sudo().search([
            ("email", "=", kw.get("email")),
            ("list_ids", "in",
             [request.env.ref('mass_mailing.mailing_list_data').id])]):
            return False
        elif request.env.user._is_public():
            visitor_sudo = (request.env['website.visitor'].sudo()
                            ._get_visitor_from_request())
            name = visitor_sudo.display_name if visitor_sudo else \
                "Website Visitor"
        else:
            name = request.env.user.partner_id.name
        request.env['mailing.contact'].sudo().create({
            "name": name,
            "email": kw.get('email'),
            "list_ids": [request.env.ref(
                'mass_mailing.mailing_list_data').id]
        })
        return True
