# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request


class WebsiteProduct(http.Controller):
    """Controller used to fetch product related data and others."""

    @http.route('/get_product_tab', auth="public", type='json',
                website=True)
    def get_product_tab(self):
        """Controller used for fetch popular products."""
        hot_deals = request.env['product.template'].sudo().search(
            [('website_published', '=', True),
             ('popular_product', '=', True)])
        response = http.Response(template='theme_autofly.popular_modal',
                                 qcontext={'hot_deals': hot_deals})
        return response.render()

    @http.route('/find_car', auth="public", type='json', website=True)
    def get_find_car(self):
        """Controller used for fetch car types."""
        hot_deals = request.env['car.types'].sudo().search([],
                                                           order='create_date desc',
                                                           limit=6)
        response = http.Response(template='theme_autofly.autofly_find_car',
                                 qcontext={'hot_deals': hot_deals})
        return response.render()

    @http.route('/get_searched_car', auth="public", type='json',
                website=True)
    def get_search_car(self):
        """Controller used for fetch car brands."""
        hot_deals = request.env['car.brand'].sudo().search([])
        response = http.Response(template='theme_autofly.autofly_search_box',
                                 qcontext={'hot_deals': hot_deals})
        return response.render()

    @http.route('/blog_snippet_autofly', auth="public", type='json',
                website=True)
    def blog_snippet_autofly(self):
        """It's used for the dynamic blog snippet."""
        return request.env['blog.post'].sudo().search_read([], limit=3)

    @http.route('/get_service_product', auth="public", type='json',
                website=True)
    def get_service_product(self):
        """Controller used for fetch service products."""
        hot_deals = request.env['product.template'].sudo().search(
            [('website_published', '=', True),
             ('detailed_type', '=', 'service')])
        response = http.Response(template='theme_autofly.service_products',
                                 qcontext={'hot_deals': hot_deals})
        return response.render()

    @http.route('/get_garage_car', auth="public", type='json',
                website=True)
    def get_garage_car(self):
        """Controller used for fetch garages."""
        hot_deals = request.env['car.garage'].sudo().search([])
        car_types = request.env['car.types'].sudo().search([])
        values = {
            'hot_deals': hot_deals,
            'car_types': car_types
        }
        response = http.Response(template='theme_autofly.portfolio_garage_page',
                                 qcontext=values)
        return response.render()

    @http.route('/get_all_type', auth="public", type='json', website=True)
    def get_all_type(self):
        """Controller used for fetch car types."""
        hot_deals = request.env['car.types'].sudo().search([])
        response = http.Response(template='theme_autofly.portfolio_type_page',
                                 qcontext={'hot_deals': hot_deals})
        return response.render()
