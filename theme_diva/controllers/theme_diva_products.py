# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ashwin T (<https://www.cybrosys.com>)
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
                'website_url': product.website_url,
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
                'url': product.website_url
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

    @http.route('/fetch_diva_products', auth="public", type='json',
                website=True)
    def fetch_diva_products(self):
        """This function is used to get the Diva products"""
        is_diva_product = request.env['product.public.category'].sudo().search(
            [('is_diva_product', '=', True)],)
        values = {
            'diva_products': is_diva_product,
            'length': len(is_diva_product)
        }
        return values

    @http.route('/shop_collection_data', type='http', auth='public', website=True, csrf=False)
    def shop_collection_data(self):
        collections = [
            {
                'title': 'British Backpacks',
                'description': 'Handmade in Britain from organic materials.',
                'image_url': '/theme_diva/static/src/images/banner-3/banner-31.jpg',
                'link': '/shop',
            },
            {
                'title': 'Adventure Inspired',
                'description': 'Organic cotton tees, printed in Britain.',
                'image_url': '/theme_diva/static/src/images/banner-3/banner-1 (3).jpg',
                'link': '/shop',
            },
            {
                'title': 'Sustainable Supplies',
                'description': 'Built for outdoor lovers. Explore responsibly.',
                'image_url': '/theme_diva/static/src/images/banner-3/banner-1 (5).jpg',
                'link': '/shop',
            },
        ]

        html = request.env['ir.ui.view']._render_template(
            "theme_diva.dynamic_shop_collection_banner",
            {'collections': collections}
        )
        return html

    @http.route('/diva_index_main_product_data', type='http', auth='public', website=True)
    def diva_index_main_product_data(self):
        products = request.env['product.template'].search([('website_published', '=', True)], limit=6)
        return request.render('theme_diva.diva_index_main_product_dynamic', {
            'main_products': products
        })
