# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import http
from odoo.http import request


class WebsiteSnippetPage(http.Controller):
    """Controller for setting routes.Pass all categories and
    category wise products as array to a template"""

    @http.route('/category/form', type='http', auth='public',
                website=True, csrf=False, sitemap=False, cache=300)
    def category_page(self, **kw):
        """Function for rendering specific category and products of that category into website"""
        category = request.env['product.category'].sudo().browse(
            int(kw.get('category_id')))
        parent = request.env['product.category'].sudo().browse(
            int(kw.get('parent_id')))
        values = {
            'category': category,
            'products': request.env['product.template'].search(
                [('categ_id', '=', category.id)]),
            'products_category': request.env['product.template'].search(
                [('category_id', '=', parent.id)])
        }
        return http.request.render(
            'website_product_search_snippet.category_snippet_img', values)

    @http.route('/selected/category/result', type='http', auth='public',
                website=True, csrf=False, sitemap=False, cache=300)
    def category_all_page(self, **kw):
        """Function for rendering specific category and products of that category into website"""
        category = request.env['product.category'].sudo().browse(
            int(kw.get('category_id')))
        values = {
            'category': category,
            'products': request.env['product.template'].search(
                [('categ_id', '=', category.id)])
        }
        return http.request.render(
            'website_product_search_snippet.all_category_snippet_img', values)

    @http.route('/selected/category/from/all_category/result', type='http', auth='public',
                website=True, csrf=False, sitemap=False, cache=300)
    def category_from_all_category_page(self, **kw):
        """Function for rendering specific category and products of that category into website"""
        category = request.env['product.category'].sudo().browse(
            int(kw.get('category_id')))
        values = {
            'category': category,
            'products': request.env['product.template'].search(
                [('categ_id', '=', category.id)])
        }
        return http.request.render(
            'website_product_search_snippet.category_from_all_category_snippet_img', values)

    @http.route('/product/form', type='http', auth='public',
                website=True, csrf=False, sitemap=False, cache=300)
    def product_page(self, **kw):
        """Function for rendering specific product into website"""
        values = {
            'products': request.env['product.template'].sudo().browse(
                int(kw.get('product_id')))
        }
        return http.request.render(
            'website_product_search_snippet.products_snippet_img', values)

    @http.route('/selected/product/from/category', type='http', auth='public',
                website=True, csrf=False, sitemap=False, cache=300)
    def selected_product_page(self, **kw):
        """Function for rendering specific product into website"""
        values = {
            'products': request.env['product.template'].sudo().browse(
                int(kw.get('product_id')))
        }
        return http.request.render(
            'website_product_search_snippet.selected_products_from_category_snippet_img',
            values)

    @http.route('/all/product/selected/product/details', type='http',
                auth='public',
                website=True, csrf=False, sitemap=False, cache=300)
    def product_all_page(self, **kw):
        """Function for rendering specific product into website"""
        values = {
            'products': request.env['product.template'].sudo().browse(
                int(kw.get('product_id')))
        }
        return http.request.render(
            'website_product_search_snippet.all_products_snippet_img', values)

    @http.route('/select/product/from/category', type='http', auth='public',
                website=True, csrf=False, sitemap=False, cache=300)
    def product_category_all_page(self, **kw):
        """Function for rendering specific product into website"""
        values = {
            'products': request.env['product.template'].sudo().browse(
                int(kw.get('product_id')))
        }
        return http.request.render(
            'website_product_search_snippet.products_category_snippet_img',
            values)

    @http.route('/product/form/all/results', type='http', auth='public',
                website=True, csrf=False, sitemap=False, cache=300)
    def product_page_result(self):
        """Function for rendering all products into website"""
        values = {
            'products': request.env['product.template'].search([])
        }
        return http.request.render(
            "website_product_search_snippet.product_all_result_template",
            values)

    @http.route('/category/form/all/results', type='http', auth='public',
                website=True, csrf=False, sitemap=False, cache=300)
    def category_page_result(self):
        """Function for rendering all categories into website"""
        values = {'category': request.env['product.category'].search(
            [('id', '!=', request.env.ref('product.product_category_all').id),
             ('id', '!=', request.env.ref('product.product_category_1').id)])}
        return http.request.render(
            "website_product_search_snippet.category_all_result_template",
            values)
