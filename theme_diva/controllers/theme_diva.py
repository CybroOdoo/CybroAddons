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
from odoo import fields, http
from odoo.http import request


class WebsiteProduct(http.Controller):
    """Controller class for handling requests related to featured products on
    the website."""

    @http.route('/get_featured_product', auth="public", type='json',
                website=True)
    def get_featured_product(self):
        """Retrieve and return information about featured products."""
        published_list_ids = request.env['product.featured'].sudo().search(
            [('is_website_published', '=', True)]).ids
        featured_products1 = (request.env['product.featured.relation']
                              .sudo().search(
            [('featured_rel_id', 'in', published_list_ids)], limit=4)
                              .product_id)
        values = {
            'featured_products1': featured_products1.read(),
            'currency_symbol': featured_products1.currency_id.symbol
        }
        return values


class FeaturedProduct(http.Controller):
    """ Controller class for handling requests related to multiple featured
    products."""

    @http.route('/get_featured_products', auth="public", type='json',
                website=True)
    def get_featured_products(self):
        """Retrieve and return information about multiple featured products"""
        published_list_ids = request.env['product.featured'].sudo().search(
            [('is_website_published', '=', True)]).ids
        featured_products2 = (request.env['product.featured.relation']
                              .sudo().search(
            [('featured_rel_id', 'in', published_list_ids)], limit=8)
                              .product_id)
        values = {
            'featured_products2': featured_products2.read(),
            'currency_symbol': featured_products2.currency_id.symbol
        }
        return values


class MainProduct(http.Controller):
    """Controller class for handling requests related to the main product."""

    @http.route('/get_main_product', auth="public", type='json',
                website=True)
    def get_main_product(self):
        """Retrieve and return information about the main product."""
        main_products = request.env['product.template'].sudo().search(
            [('website_published', '=', True)],
            order='create_date asc', limit=1)
        values = {
            'main_products': main_products.read(),
        }
        return values


class WebsiteBlog(http.Controller):
    """Controller class for handling requests related to blog posts on the
    website."""

    @http.route('/get_blog_post', auth="public", type='json',
                website=True)
    def get_blog_post(self):
        """Retrieve and return information about recent blog posts."""
        posts = request.env['blog.post'].sudo().search(
            [('website_published', '=', True),
             ('post_date', '<=', fields.Datetime.now())],
            order='published_date desc', limit=3)
        values = {
            'posts_recent': posts.read(
                ['name', 'published_date', 'blog_id', 'cover_properties']),
        }
        return values

    @http.route('/get_blog_posts', auth="public", type='json',
                website=True)
    def get_blog_posts(self):
        """Retrieve and return information about multiple recent blog posts."""
        posts = request.env['blog.post'].sudo().search(
            [('website_published', '=', True),
             ('post_date', '<=', fields.Datetime.now())],
            order='published_date desc', limit=4)
        values = {
            'posts_recent': posts.read(
                ['name', 'published_date', 'blog_id', 'cover_properties']),
        }
        return values
