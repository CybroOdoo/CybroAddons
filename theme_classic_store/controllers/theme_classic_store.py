# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vivek @ cybrosys,(odoo@cybrosys.com)
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
from odoo import fields, http
from odoo.http import request


class WebsiteClassicCategory(http.Controller):
    """
    This controller method returns a JSON object that categorizes products based
     on their product categories.
    :return: a JSON object containing the main product categories and their
    respective product counts
    :rtype: dict
    """

    @http.route('/classic_product_category', auth="public", type='json')
    def get_product_categories(self):
        """
        Categorize products based on product categories
        The counter "category_counter" is used to keep track of the product
        count in each category
        """
        product_ids = request.env['product.template'].sudo().search(
            [('website_published', '=', True)])
        product_category_ids = request.env[
            'product.public.category'].sudo().search([])
        product_categories_main_list = [rec for rec in product_category_ids if
                                        rec.child_id]
        category_counter = {rec: 0 for rec in product_category_ids}
        for rec in product_ids:
            for cat in rec.public_categ_ids:
                if cat in product_category_ids:
                    category_counter[cat] += 1
        values = {
            'product_categories_main': product_categories_main_list,
            'counter': category_counter
        }
        response = http.Response(
            template='theme_classic_store.s_classic_store_categories',
            qcontext=values)
        return response.render()


class WebsiteClassicTrending(http.Controller):
    """
    This module defines a controller for the website that showcases trending
    products.
    It contains a class `WebsiteClassicTrending` with a method
    `get_trending_products()`
    that is called when the route `/classic_product_trending` is accessed.
    """

    @http.route('/classic_product_trending', auth="public", type='json',
                website=True)
    def get_trending_products(self):
        """
        Showcase trending products based on their number of views between a
        defined period
        number of views for a product is tracked and then the most viewed
        products are shown in order of views
        """
        classic_config = request.env[
            'classic.store.config'].sudo().search([])
        trending_products = classic_config.trending_product_ids
        if not trending_products:
            products = request.env['product.template'].sudo().search([])
            for product in products:
                product.views = 0
                product.most_viewed = False
            date = fields.Datetime.now()
            date_before = date - datetime.timedelta(days=7)
            products = request.env['website.track'].sudo().search(
                [('visit_datetime', '<=', date),
                 ('visit_datetime', '>=', date_before),
                 ('product_id', '!=', False)])
            for product in products:
                product.product_id.views = product.product_id.views + 1
            trending_products = request.env['product.template'].sudo().search(
                [('is_published', '=', True),
                 ('views', '!=', 0)],
                order='views desc', limit=4)
        values = {
            'trending_products': trending_products
        }
        response = http.Response(
            template='theme_classic_store.s_classic_store_trending',
            qcontext=values)
        return response.render()
