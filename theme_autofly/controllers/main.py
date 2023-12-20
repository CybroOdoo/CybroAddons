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
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class About(http.Controller):
    """Controller for about page, portfolio page, team page, service page."""

    @http.route('/about', website=True, type='http', auth='public',
                csrf=False)
    def about_page(self):
        """Used for the about page."""
        return request.render('theme_autofly.about_page')

    @http.route('/portfolio', website=True, type='http', auth='public',
                csrf=False)
    def portfolio_page(self):
        """Used for the portfolio page."""
        return request.render('theme_autofly.portfolio_page')

    @http.route('/team', website=True, type='http', auth='public',
                csrf=False)
    def team_page(self):
        """Used for the team page."""
        return request.render('theme_autofly.team_page')

    @http.route('/service', website=True, type='http', auth='public',
                csrf=False)
    def service_page(self):
        """Used for the service page."""
        return request.render('theme_autofly.service_page')

    @http.route('/blog_snippet', auth="public", type='json', website=True)
    def latest_blog(self):
        """Used for the dynamic blog snippet."""
        return request.env['blog.post'].sudo().search_read([], limit=3)

    @http.route('/autofly/service', website=True, auth='public',
                csrf=False)
    def service_booking(self, **kwargs):
        """Used for the service page."""
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
        hot_deals = request.env['product.template'].sudo().search(
            [('car_brand_id', '=', int(kwargs.get('car-selection'))),
             ('car_type_id', '=',
              int(kwargs.get('car-type-selection'))),
             ('location', '=', kwargs.get('car-location')),
             ('list_price', '=', float(kwargs.get('car-price'))),
             ('car_model', '=', kwargs.get('car-model'))])
        return request.render('theme_autofly.specific_car',
                              qcontext={'hot_deals': hot_deals})
