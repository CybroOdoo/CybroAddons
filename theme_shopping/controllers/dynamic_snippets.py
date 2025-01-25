# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request


class DynamicSnippets(http.Controller):
    """This class is for the getting values for dynamic product snippets
       """
    @http.route('/top_deal_product_snippet', auth='public', type='json',
                website=True)
    def get_best_products(self):
        """Controller to reflect chosen products in 'Top Deal'
         snippet"""
        products = []
        products_search_read = request.env['product.product'].with_user(
            1).search_read(
            [('is_published', '=', True),
             ('is_top_deal_product', '=', True),
             ('ready_to_top_deal', '=', True)],
            ['name', 'image_1920', 'website_id',
             'sales_count', 'list_price','actual_price', 'offer_price', 'product_tmpl_id', 'website_url'])
        unique_products = []
        seen_tmpl_ids = set()
        for product in products_search_read:
            if product['product_tmpl_id'][0] not in seen_tmpl_ids:
                unique_products.append(product)
                seen_tmpl_ids.add(product['product_tmpl_id'][0])
        for product in unique_products:
            products.append(product)
        response = http.Response(
            template='theme_shopping.best_deal_product_carousel_snippet',
            qcontext={'products': products})
        return products

    @http.route('/get_winter_product_snippet', auth='public', type='json',
                website=True)
    def get_winter_products(self):
        """Controller to reflect chosen products in 'Winter Collection'
         snippet"""
        products = []
        products_search_read = request.env['product.product'].with_user(
            1).search_read(
            [('is_published', '=', True),
             ('categ_id', '=', request.env.ref(
                'theme_shopping.product_category_winter').id)],
            ['name', 'image_1920', 'website_id',
             'sales_count', 'list_price', 'website_url'])
        for product in products_search_read:
            products.append(product)

        response = http.Response(
            template='theme_shopping.winter_product_carousel_snippet',
            qcontext={'products': products})
        return products
