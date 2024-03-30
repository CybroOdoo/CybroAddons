# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
###############################################################################
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class About(http.Controller):
    """controller for the about page, portfolio page, team page, service
    page"""

    @http.route('/about', website=True, type='http',
                auth='public', csrf=False)
    def about_page(self):
        """It's used for the about page"""
        return request.render('theme_autofly.about_page')

    @http.route('/portfolio', website=True, type='http', auth='public',
                csrf=False)
    def portfolio_page(self):
        """It's used for the portfolio page"""
        return request.render('theme_autofly.portfolio_page')

    @http.route('/team', website=True, type='http',
                auth='public', csrf=False)
    def team_page(self):
        """It's used for the team page"""
        return request.render('theme_autofly.team_page')

    @http.route('/service', website=True, type='http', auth='public',
                csrf=False)
    def service_page(self):
        """It's used for the service page"""
        return request.render('theme_autofly.service_page')

    @http.route('/blog_snippet', auth="public", type='json', website=True)
    def latest_blog(self):
        """It's used for the dynamic blog snippet"""
        return request.env['blog.post'].sudo().search_read([], limit=3)

    @http.route(['/total_product_sold'], type="json", auth="public")
    def sold_total(self):
        """Controller used for fetch sold products"""
        total_sold = sum(request.env['sale.order'].sudo().search([
            ('state', 'in', ['done', 'sale'])]).mapped(
            'order_line.product_uom_qty'))
        return total_sold

    @http.route('/autofly/service',
                website=True, auth='public', csrf=False)
    def service_booking(self, **kwargs):
        """It's used for the service page"""
        request.env['service.booking'].sudo().create({
            'name': kwargs.get('usr1'),
            'email': kwargs.get('email'),
            'description': kwargs.get('text')
        })
        return request.render('theme_autofly.service_page')

    @http.route('/cars-search', website=True, type='http', auth='public',
                csrf=False)
    def car_search(self, **kwargs):
        """Handle dynamic car search."""
        try:
            domain = []
            car_brand = int(
                kwargs.get('car-selection')) if kwargs.get(
                'car-selection') != 'select brand' else False
            car_type = int(
                kwargs.get('car-type-selection')) if kwargs.get(
                'car-type-selection') != 'select type' else False
            car_location = kwargs.get(
                'car-location') if kwargs.get('car-location') != '' else False
            car_price = float(
                kwargs.get('car-price')) if kwargs.get(
                'car-price') != '' else False
            car_model = kwargs.get(
                'car-model') if kwargs.get('car-model') != '' else False

            if car_brand:
                domain.append(('car_brand', '=', car_brand))
            if car_type:
                domain.append(('car_type', '=', car_type))
            if car_location:
                domain.append(('location', '=', car_location))
            if car_price:
                domain.append(('list_price', '=', car_price))
            if car_model:
                domain.append(('car_model', '=', car_model))
            if len(domain) == 0:
                return request.render('theme_autofly.specific_car', qcontext=[])

            hot_deals = request.env['product.template'].sudo().search(domain)

            values = {
                'hot_deals': hot_deals,
            }
        except:
            return request.render('theme_autofly.specific_car', qcontext=[])
        return request.render('theme_autofly.specific_car', qcontext=values)

    @http.route(
        '/get-company/address', type='json', auth="public", website=True)
    def get_company_address(self):
        user_id = request.env.user
        return ' '.join(filter(None, (
            user_id.company_id.street, user_id.company_id.city,
            user_id.company_id.state_id.display_name,
            user_id.company_id.country_id.display_name)))
