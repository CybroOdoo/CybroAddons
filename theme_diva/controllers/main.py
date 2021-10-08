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

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http, fields
from odoo.http import request


class WebsiteSaleExtend(WebsiteSale):
    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        """
        Overrided function to update the response with featured products objects.Here we are updating qcontext.
        :param page:
        :param category:
        :param search:
        :param ppg:
        :param post:
        :return:
        """
        response = super(WebsiteSaleExtend, self).shop(page=page,
                                                       category=category,
                                                       search=search, ppg=ppg,
                                                       **post)
        env = request.env
        published_list_ids = env['product.featured'].sudo().search(
            [('website_published', '=', True)]).ids
        featured_products = env['product.featured.relation'].sudo().search(
            [('featured_rel', 'in', published_list_ids)], limit=3)
        response.qcontext.update({
            'featured_products': featured_products,
        })
        return response


class WebsiteProduct(http.Controller):

    @http.route('/get_featured_product', auth="public", type='json',
                website=True)
    def get_featured_product(self):
        env = request.env
        published_list_ids = env['product.featured'].sudo().search(
            [('website_published', '=', True)]).ids
        featured_products1 = env['product.featured.relation'].sudo().search(
            [('featured_rel', 'in', published_list_ids)], limit=4)
        values = {
            'featured_products1': featured_products1,
        }
        response = http.Response(template='theme_diva.diva_index_features',
                                 qcontext=values)
        return response.render()


class FeaturedProduct(http.Controller):

    @http.route('/get_featured_products', auth="public", type='json',
                website=True)
    def get_featured_products(self):
        env = request.env
        published_list_ids = env['product.featured'].sudo().search(
            [('website_published', '=', True)]).ids
        featured_products2 = env['product.featured.relation'].sudo().search(
            [('featured_rel', 'in', published_list_ids)], limit=8)

        values = {
            'featured_products2': featured_products2,
        }
        response = http.Response(template='theme_diva.diva_index2_features',
                                 qcontext=values)
        return response.render()


# class PopularProduct(http.Controller):
#
#     @http.route('/get_popular_product', auth="public", type='json',
#                 website=True)
#     def get_popular_product(self):
#         popular_products = request.env['product.template'].sudo().search(
#             [('website_published', '=', True)],
#             order='create_date asc', limit=4)
#
#         values = {
#             'popular_products': popular_products,
#         }
#         response = http.Response(template='theme_diva.diva_popular_product',
#                                  qcontext=values)
#         return response.render()


class MainProduct(http.Controller):

    @http.route('/get_main_product', auth="public", type='json',
                website=True)
    def get_main_product(self):
        main_products = request.env['product.template'].sudo().search(
            [('website_published', '=', True)],
            order='create_date asc', limit=1)

        values = {
            'main_products': main_products,
        }
        response = http.Response(template='theme_diva.diva_index_main_product',
                                 qcontext=values)
        return response.render()


# class WebsiteNew(Website):
#
#     @http.route('/', type='http', auth="public", website=True, sitemap=True)
#     def index(self, echelle='header1', **kw):
#         response = super(WebsiteNew, self).index(echelle=echelle, **kw)
#         response.qcontext.update({
#             'new_header': echelle,
#         })
#         return response
