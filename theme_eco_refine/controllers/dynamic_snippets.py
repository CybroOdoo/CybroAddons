# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sabeel B (odoo@cybrosys.com)
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
################################################################################
import time
from odoo import http
from odoo.http import request


class TopSellingProducts(http.Controller):
    """This class is for the getting top most sold products
        products_categories:
                          function for passing top most sold products to js,
                          and it returns products,unique categories and the
                           current website
    """

    @http.route('/bestsellers', auth='public', type='json', website=True)
    def get_bestseller(self, products_per_slide=4):
        """Function for getting the current website, top most sold products and
        its categories.
        Return:
            - products: Most sold products
            - unique_categories: Categories of all products
            - current_website: The current website for checking products or
            categories are available in that website
        """
        current_website = request.env['website'].sudo().get_current_website().id
        public_categ_id = request.env[
            'product.public.category'].sudo().search_read([], ['name',
                                                               'website_id'])
        products = []
        public_categories = []
        for category in public_categ_id:
            products_search_read = request.env['product.template'].with_user(
                1).search_read(
                [('is_published', '=', True),
                 ('public_categ_ids.id', '=', category['id'])],
                ['name', 'image_1920', 'public_categ_ids', 'website_id',
                 'sales_count', 'list_price'],
                order='sales_count'
            )
            for product in products_search_read:
                if product['sales_count'] != 0:
                    products.append(product)
                    public_categories.append(category)
        unique_categories = [dict(categories) for categories in
                             {tuple(sorted(record.items())) for record in
                              public_categories}]
        products = sorted(products, key=lambda i: i['sales_count'],
                          reverse=True)
        records_grouped = []
        record_list = []
        for index, record in enumerate(products, 1):
            record_list.append(record)
            if index % products_per_slide == 0:
                records_grouped.append(record_list)
                record_list = []
        if any(record_list):
            records_grouped.append(record_list)

        response = http.Response(
            template='theme_eco_refine.best_seller_template',
            qcontext={
                'products': products,
                'categories': unique_categories[0],
                'current_website_id': current_website,
                'products_per_slide': products_per_slide,
                'num_slides': len(records_grouped),
                "uniqueId": "pc-%d" % int(time.time() * 1000),
                'products_list': records_grouped
            }
        )
        return response.render()

    @http.route('/new_arrivals', auth='public', type='json', website=True)
    def get_new_arrivals(self, products_per_slide=4):
        """Function for getting the current website,new arrival products and
               its categories.
                Return
                      products-most sold products
                      unique_categories-categories of all products
                      current_website-the current website for checking products
            """
        current_website = request.env[
            'website'].sudo().get_current_website().id
        public_categ_id = request.env[
            'product.public.category'].sudo().search_read([], ['name',
                                                               'website_id'])
        products = []
        public_categories = []
        for category in public_categ_id:
            products_search_read = request.env['product.template'].with_user(
                1).search_read(
                [('is_published', '=', True),
                 ('public_categ_ids.id', '=', category['id'])],
                ['name', 'public_categ_ids', 'website_id',
                 'sales_count', 'image_1920', 'list_price', 'create_date'],
                order='create_date desc'
            )
            for product in products_search_read:
                # if product['sales_count'] != 0:
                products.append(product)
                public_categories.append(category)
        unique_categories = [dict(categories) for categories in
                             {tuple(sorted(record.items())) for record in
                              public_categories}]
        products = sorted(products, key=lambda i: i['create_date'],
                          reverse=True)
        records_grouped = []
        record_list = []
        for index, record in enumerate(products, 1):
            record_list.append(record)
            if index % products_per_slide == 0:
                records_grouped.append(record_list)
                record_list = []
        if any(record_list):
            records_grouped.append(record_list)

        response = http.Response(
            template='theme_eco_refine.new_product_arrival',
            qcontext={'products': products,
                      'categories': unique_categories[0],
                      'current_website_id': current_website,
                      'products_per_slide': products_per_slide,
                      'num_slides': len(records_grouped),
                      'products_list': records_grouped})
        return response.render()

    @http.route('/top_rated', auth='public', type='json', website=True)
    def get_top_rated(self, products_per_slide=4):
        """Function for getting the current website,rated products and
                  its categories.
                   Return
                         products-most sold products
                         unique_categories-categories of all products
                         current_website-the current website for checking
                         products or"""
        current_website = request.env[
            'website'].sudo().get_current_website().id
        rated_products = request.env['rating.rating'].sudo().search_read(
            [('res_model', '=', 'product.template')], ['res_id', 'res_name', ],
            order='rating desc')

        products = []
        public_categories = []
        for category in rated_products:
            products_search_read = request.env['product.template'].with_user(
                1).search_read(
                [('is_published', '=', True),
                 ('id', '=', category['res_id'])],
                ['name', 'public_categ_ids', 'website_id',
                 'sales_count', 'image_1920', 'list_price', 'create_date'],

            )
            for product in products_search_read:
                products.append(product)
                public_categories.append(category)
        unique_categories = [dict(categories) for categories in
                             {tuple(sorted(record.items())) for record in
                              public_categories}]
        records_grouped = []
        record_list = []
        for index, record in enumerate(products, 1):
            record_list.append(record)
            if index % products_per_slide == 0:
                records_grouped.append(record_list)
                record_list = []
        if any(record_list):
            records_grouped.append(record_list)
        response = http.Response(
            template='theme_eco_refine.top_rated_products',
            qcontext={'products': products,
                      'categories': unique_categories[0] if unique_categories
                      else [],
                      'current_website_id': current_website,
                      'products_per_slide': products_per_slide,
                      "uniqueId": "uc-%d" % int(time.time() * 1000),
                      'num_slides': len(records_grouped),
                      'products_list': records_grouped})
        return response.render()
