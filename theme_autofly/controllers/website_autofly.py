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
from odoo import http
from odoo.http import request


class WebsiteAutoFly(http.Controller):
    """Controller used to fetch product related data and also for about page,
     portfolio page, team page, service page."""

    @http.route('/about', website=True, type='http', auth='public',
                csrf=False)
    def about_page(self):
        """Render the about page."""
        return request.render('theme_autofly.about_page')

    @http.route('/portfolio', website=True, type='http', auth='public',
                csrf=False)
    def portfolio_page(self):
        """Render the portfolio page."""
        return request.render('theme_autofly.portfolio_page')

    @http.route('/team', website=True, type='http', auth='public',
                csrf=False)
    def team_page(self):
        """Render the team page."""
        return request.render('theme_autofly.team_page')

    @http.route('/service', website=True, type='http', auth='public',
                csrf=False)
    def service_page(self):
        """Render the service page."""
        return request.render('theme_autofly.service_page')

    @http.route('/blog_snippet', auth="public", type='json')
    def latest_blog(self):
        """Return the data for dynamic blog snippet."""
        return request.env['blog.post'].sudo().search_read(
            [], ['name', 'blog_id', 'subtitle', 'published_date'],
            order='id desc', limit=3)

    @http.route('/get_testimonial', auth="public", type='json')
    def get_testimonial(self):
        """Return the data for testimonial snippet."""
        testimonial = request.env['autofly.testimonial'].sudo().search(
            [], order='id desc', limit=12)
        values = {
            f'slide{i + 1}': [{'id': record.id,
                               'name': record.display_name,
                               'partner_id': record.partner_id.id,
                               'rating': record.rating,
                               'review': record.review,
                               } for record in testimonial[i * 3:(i + 1) * 3]]
            for i in range((len(testimonial) + 2) // 3)
        }
        return values

    @http.route('/autofly/service', type='http', website=True, auth='public',
                csrf=False)
    def service_booking(self, **kwargs):
        """Render the service page."""
        request.env['service.booking'].sudo().create({
            'name': kwargs.get('usr1'),
            'email': kwargs.get('email'),
            'description': kwargs.get('text')
        })
        return request.render('theme_autofly.service_page')

    @http.route('/cars-search', website=True, type='http', auth='public',
                csrf=False)
    def car_search(self, **kwargs):
        """Used for searching particular cars."""
        domain = []
        if kwargs.get('car-selection'):
            domain.append(
                ('car_brand_id', '=', int(kwargs.get('car-selection'))))
        if kwargs.get('car-type-selection'):
            domain.append(('car_type_id', '=', int(kwargs.get(
                'car-type-selection'))))
        if kwargs.get('car-price'):
            domain.append(('list_price', '=', float(kwargs.get('car-price'))))
        if kwargs.get('car-model'):
            domain.append(
                ('car_model', '=', int(float(kwargs.get('car-model')))))
        if kwargs.get('car-location'):
            domain.append(('location', 'ilike', kwargs.get('car-location')))
        result = request.env['product.template'].sudo().search(domain)
        return request.render('theme_autofly.specific_car',
                              qcontext={'hot_deals': result})

    @http.route('/get_product_tab', auth="public", type='json')
    def get_product_tab(self):
        """Controller used to Fetch popular products."""
        hot_deals = request.env['product.template'].sudo().search([
            ('website_published', '=', True),
            ('popular_product', '=', True)])
        response = http.Response(template='theme_autofly.popular_modal',
                                 qcontext={'hot_deals': hot_deals})
        return response.render()

    @http.route('/find_car', auth="public", type='json')
    def get_find_car(self):
        """Controller used to fetch car types."""
        hot_deals = request.env['car.types'].sudo().search([],
                                                           order='id desc',
                                                           limit=6)
        response = http.Response(template='theme_autofly.autofly_find_car',
                                 qcontext={'hot_deals': hot_deals})
        return response.render()

    @http.route('/get_searched_car', auth="public", type='json')
    def get_search_car(self):
        """Controller used to fetch car brands."""
        brands = request.env['car.brand'].sudo().search([])
        types = request.env['car.types'].sudo().search([])
        brand = [{'id': record.id, 'name': record.name} for record in brands]
        car_type = [{'id': record.id, 'name': record.name} for record in types]
        return {'type': car_type, 'brand': brand}

    @http.route('/get_service_product', auth="public", type='json')
    def get_service_product(self):
        """Controller used to fetch service products."""
        hot_deals = request.env['product.template'].sudo().search([
            ('website_published', '=', True),
            ('detailed_type', '=', 'service')])
        response = http.Response(template='theme_autofly.service_products',
                                 qcontext={'hot_deals': hot_deals})
        return response.render()

    @http.route('/get_garage_car', auth="public", type='json')
    def get_garage_car(self):
        """Controller used to fetch garages."""
        hot_deals = request.env['car.garage'].sudo().search([])
        car_types = request.env['car.types'].sudo().search([])
        values = {'hot_deals': hot_deals, 'car_types': car_types}
        response = http.Response(template='theme_autofly.portfolio_garage_page',
                                 qcontext=values)
        return response.render()

    @http.route('/get_all_type', auth="public", type='json')
    def get_all_type(self):
        """Controller used to fetch car types."""
        hot_deals = request.env['car.types'].sudo().search([])
        response = http.Response(template='theme_autofly.portfolio_type_page',
                                 qcontext={'hot_deals': hot_deals})
        return response.render()
