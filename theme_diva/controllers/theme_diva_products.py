# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (<https://www.cybrosys.com>)
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


class WebsiteProduct(http.Controller):

    @http.route('/get_featured_product', auth="public", type='json',
                website=True)
    def get_featured_product(self):
        """This function is used to get the featured products"""
        published_list_ids = request.env['product.featured'].sudo().search(
            [('website_published', '=', True)]).ids
        # Use mapped('product_id') to get a list of product records
        featured_products1 = request.env[
            'product.featured.relation'].sudo().search(
            [('featured_rel_id', 'in', published_list_ids)], limit=4).mapped(
            'product_id')
        products = []
        for product in featured_products1:
            val = {
                'product': product.id,
                'list_price': product.list_price,
                'name': product.name,
                'currency': product.currency_id.symbol,
                'rating_count': product.rating_count,
                'rating_total': product.rating_total,
            }
            products.append(val)
        values = {
            'featured_products1': products,
        }
        return values

    @http.route('/get_featured_products', auth="public", type='json',
                website=True)
    def get_featured_products(self):
        """This function is used to get the featured products"""
        published_list_ids = request.env['product.featured'].sudo().search(
            [('website_published', '=', True)]).ids
        featured_products2 = request.env['product.featured.relation'].sudo().search(
            [('featured_rel_id', 'in', published_list_ids)], limit=8).mapped('product_id')
        products = []
        for product in featured_products2:
            val = {
                'product': product.id,
                'list_price':product.list_price,
                'name': product.name,
                'currency': product.currency_id.symbol,
            }
            products.append(val)
        values = {
            'featured_products2': products,
        }
        return values

    @http.route('/get_main_product', auth="public", type='json',
                website=True)
    def get_main_product(self):
        """This function is used to get the main products"""
        main_products = request.env['product.template'].sudo().search(
            [('website_published', '=', True)],
            order='create_date asc', limit=1)
        values = {
            'main_products': main_products.read(),
        }
        return values
