# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import datetime

from odoo import http
from odoo.http import request
from odoo import fields


class WebsiteProduct(http.Controller):
    """Class for dynamic snippets for products"""

    @http.route('/get_featured_product', auth='public', type='json',
                website=True)
    def get_featured_products(self):
        """Function to get featured products"""
        silon_configuration = request.env.ref(
            'theme_silon.silon_configuration_data')
        product_id = silon_configuration.featured_product_ids
        rating = request.website.viewref('website_sale.product_comment').active
        res = {'products': []}
        for product in product_id:
            combination_info = product._get_combination_info_variant()
            res_product = product.read(['id', 'name', 'website_url',
                                        'rating_avg', 'rating_count'])[0]
            res_product['ratings'] = round(res_product['rating_avg'], 2)
            res_product['rating'] = rating
            res_product.update(combination_info)
            res['products'].append(res_product)
        products = res['products']
        values = {'products': products}
        response = http.Response(
            template='theme_silon.featured_product_snippet', qcontext=values)
        return response.render()

    @http.route('/get_popular_product', auth='public', type='json',
                website=True)
    def get_popular_products(self):
        """Function to get Popular Products"""
        products = request.env['product.template'].sudo().search([])
        for each in products:
            each.qty_sold = 0
            each.top_selling = False
        date = fields.Datetime.now()
        date_before = date - datetime.timedelta(days=7)
        orders = request.env['sale.order'].sudo().search([
            ('date_order', '<=', date),
            ('date_order', '>=',
             date_before),
            ('website_id', '!=', False),
            ('state', 'in', (
                'sale', 'done'))])
        for order in orders:
            order_line = order.order_line
            for product in order_line:
                product.product_id.qty_sold = product.product_id.qty_sold + 1
        website_product_ids = request.env['product.template'].sudo().search(
            [('is_published', '=', True),
             ('qty_sold', '!=', 0)],
            order='qty_sold desc', limit=4)

        website_product_ids.top_selling = True
        rating = request.website.viewref('website_sale.product_comment').active
        res = {'products': []}
        for product in website_product_ids:
            combination_info = product._get_combination_info()
            res_product = product.read(['id', 'name', 'website_url',
                                        'rating_avg', 'rating_count'])[0]
            res_product['ratings'] = round(res_product['rating_avg'], 2)
            res_product['rating'] = rating
            res_product.update(combination_info)
            res['products'].append(res_product)
        products = res['products']
        values = {'website_product_ids': products}
        response = http.Response(
            template='theme_silon.popular_snippet', qcontext=values)
        return response.render()

    @http.route('/get_trending_product', auth='public', type='json',
                website=True)
    def get_trending_product(self):
        """Function to get Trending Products"""
        products = request.env['product.template'].sudo().search([])
        for each in products:
            each.views = 0
            each.most_viewed = False
        date = fields.Datetime.now()
        date_before = date - datetime.timedelta(days=7)
        products = request.env['website.track'].sudo().search(
            [('visit_datetime', '<=', date),
             ('visit_datetime', '>=', date_before),
             ('product_id', '!=', False)])
        for pro in products:
            pro.product_id.views = pro.product_id.views + 1

        product_ids = request.env['product.template'].sudo().search(
            [('is_published', '=', True),
             ('views', '!=', 0)],
            order='views desc', limit=8)

        product_ids.most_viewed = True
        rating = request.website.viewref('website_sale.product_comment').active
        res = {'products': []}
        for product in product_ids:
            combination_info = product._get_combination_info()
            res_product = product.read(['id', 'name', 'website_url',
                                        'rating_avg', 'rating_count'])[0]
            res_product['ratings'] = round(res_product['rating_avg'], 2)
            res_product['rating'] = rating
            res_product.update(combination_info)
            res['products'].append(res_product)
        products = res['products']
        values = {'product_ids': products}
        response = http.Response(
            template='theme_silon.trending_snippet', qcontext=values)
        return response.render()
