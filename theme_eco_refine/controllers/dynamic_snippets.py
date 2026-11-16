# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import time
from datetime import timedelta

from odoo import fields, http
from odoo.http import request


class DynamicSnippets(http.Controller):
    """This class is for the getting values for dynamic product snippets
       """

    @http.route('/top_selling_products', type='jsonrpc', auth='public')
    def top_selling(self):
        """Function for getting the current website,top sold products and
           its categories.
            Return
                  products-most sold products
                  unique_categories-categories of all products
                  current_website-the current website for checking products or
            """
        current_website = request.env.website or request.env['website'].browse(
            request.env.context['host_id'])
        public_categ_id = request.env[
            'product.public.category'].sudo().search_read([], ['name',
                                                               'website_id'])
        # product.template.sales_count is 0 for users outside the salesman
        # group (and sudo() keeps the public user), so the sold quantities
        # are read from sale.report directly, like Odoo does (done orders of
        # the last 365 days).
        report = request.env['sale.report'].sudo()
        sold = {
            template.id: qty for template, qty in report._read_group(
                [('state', 'in', report._get_done_states()),
                 ('date', '>=', fields.Date.today() - timedelta(days=365))],
                ['product_tmpl_id'], ['product_uom_qty:sum'])
        }
        products = []
        public_categories = []
        for category in public_categ_id:
            products_search_read = request.env['product.template'].sudo().search_read(
                [('is_published', '=', True),
                 ('public_categ_ids.id', '=', category['id'])],
                ['name', 'image_1920', 'public_categ_ids', 'website_id',
                 'sales_count', 'list_price']
            )
            for product in products_search_read:
                product['sales_count'] = sold.get(product['id'], 0)
            products_search_read.sort(key=lambda p: p.get('sales_count', 0),
                                      reverse=True)
            for product in products_search_read:
                if product['sales_count'] != 0:
                    products.append(product)
                    public_categories.append(category)
        unique_categories = [dict(categories) for categories in
                             {tuple(sorted(record.items())) for record in
                              public_categories}]
        products = sorted(products, key=lambda i: i['sales_count'],
                          reverse=True)
        unique_id = "pc-%d" % int(time.time() * 1000)
        return products, unique_categories, current_website, unique_id

    @http.route('/new_arrival_products', type='jsonrpc', auth='public')
    def products_new_arrivals(self):
        """Function for getting the current website,new arrival products and
           its categories.
            Return
                  products-most sold products
                  unique_categories-categories of all products
                  current_website-the current website for checking products or
        """
        current_website = request.env.website or request.env['website'].browse(
            request.env.context['host_id'])
        public_categ_id = request.env[
            'product.public.category'].sudo().search_read([], ['name',
                                                               'website_id'])
        products = []
        public_categories = []
        for category in public_categ_id:
            products_search_read = request.env['product.template'].sudo().search_read(
                [('is_published', '=', True),
                 ('public_categ_ids.id', '=', category['id'])],
                ['name', 'public_categ_ids', 'website_id',
                 'sales_count', 'image_1920', 'list_price', 'create_date'],
                order='create_date desc')
            for product in products_search_read:
                products.append(product)
                public_categories.append(category)
        unique_id = "uc-%d" % int(time.time() * 1000)
        unique_categories = [dict(categories) for categories in
                             {tuple(sorted(record.items())) for record in
                              public_categories}]
        products = sorted(products, key=lambda i: i['create_date'],
                          reverse=True)
        return products, unique_categories, current_website, unique_id

    @http.route('/top_rated_products', type='jsonrpc', auth='public')
    def top_rated_products(self):
        """Function for getting the current website, rated products and
           its categories.
            Return
                  products-published products that have ratings
                  unique_categories-categories of the rated products
                  current_website-the current website for checking products
                  unique_id-identifier used for the snippet tabs
        """
        current_website = request.env.website or request.env['website'].browse(
            request.env.context['host_id'])
        ratings = request.env['rating.rating'].sudo().search_read(
            [('res_model', '=', 'product.template')],
            ['res_id'], order='rating desc')
        rated_ids = []
        for rating in ratings:
            if rating['res_id'] not in rated_ids:
                rated_ids.append(rating['res_id'])
        products_by_id = {
            product['id']: product
            for product in request.env['product.template'].sudo().search_read(
                [('is_published', '=', True), ('id', 'in', rated_ids)],
                ['name', 'public_categ_ids', 'website_id', 'sales_count',
                 'image_1920', 'list_price', 'create_date'])
        }
        products = [products_by_id[res_id] for res_id in rated_ids
                    if res_id in products_by_id]
        category_ids = {categ_id for product in products
                        for categ_id in product['public_categ_ids']}
        unique_categories = request.env['product.public.category'].sudo(
        ).search_read([('id', 'in', list(category_ids))],
                      ['name', 'website_id'])
        unique_id = "tr-%d" % int(time.time() * 1000)
        return products, unique_categories, current_website, unique_id