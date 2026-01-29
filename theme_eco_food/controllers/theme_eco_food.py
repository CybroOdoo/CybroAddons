# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from odoo import http
from odoo.http import request


class WebsiteEcoFood(http.Controller):

    @http.route('/add_to_cart/<int:pid>', auth="public", type='http',
                website=True)
    def add_to_cart(self, pid):
        """this function is used to add items to cart from snippet"""
        product = request.env['product.product'].search(
            [('product_tmpl_id', '=', pid)])[0]
        order = request.website.sale_get_order(force_create=True)
        order._cart_update(
            product_id=product.id,
            add_qty=1,
        )
        return request.redirect('/shop/cart')

    @http.route('/add_to_wishlist_new_arrival/<int:product_id>', auth="public",
                type='http', website=True)
    def add_to_wishlist(self, product_id):
        """this function is used to add items to wishlist from snippet"""
        product_ids = request.env['product.template'].browse(
            product_id)._create_first_product_variant().id
        pricelist = request.website.pricelist_id
        product = request.env['product.product'].browse(product_ids)
        price = product._get_combination_info_variant(
            pricelist=pricelist,
        )['price']
        partner_id = request.env.user.partner_id.id if not (
            request.website.is_public_user()) else False
        wish = request.env['product.wishlist'].sudo()._add_to_wishlist(
            pricelist.id,
            pricelist.currency_id.id,
            request.website.id,
            price,
            product_ids,
            partner_id
        )
        if not partner_id:
            request.session['wishlist_ids'] = request.session.get(
                'wishlist_ids', []) + [wish.id]
        return request.redirect('/shop/wishlist')

    @http.route('/get_best_seller', auth="public", type='json', website=True)
    def get_best_seller(self):
        """this function is used to retrieve the best-selling product"""
        products = request.env.ref(
            'theme_eco_food.dynamic_product_best_seller'
        ).product_tmpl_ids.sorted(
            key=lambda x: x.sales_count, reverse=True)[:10]
        best_seller = [{'id': product.id,
                        'name': product.name,
                        'category': product.categ_id.name,
                        'rating_avg': product.rating_avg,
                        'list_price': product.list_price,
                        'currency': product.currency_id.symbol
                        } for product in products]
        return best_seller

    @http.route('/get_featured_products', auth="public", type='json',
                website=True)
    def get_featured_products(self):
        """this function is used to retrieve featured products"""
        products = request.env.ref(
            'theme_eco_food.featured_product_new').featured_products_ids.sorted(
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

    @http.route('/get_recently_added_products', auth="public", type='json',
                website=True)
    def get_recently_added_products(self):
        """this function will return the most recently added products."""
        products = request.env.ref(
            'theme_eco_food.recently_added_product_recently_new'
        ).recent_products_ids.sorted(
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

    @http.route('/eco_food_new_arrivals', auth="public", type='json',
                website=True)
    def eco_food_new_arrivals(self):
        """this function is used to retrieve new arrival products"""
        products = request.env.ref(
            'theme_eco_food.new_arrival_new').new_arrivals_ids.sorted(
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
