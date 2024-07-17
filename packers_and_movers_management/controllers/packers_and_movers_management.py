# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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
from math import cos, sin, asin, sqrt, radians
from geopy import Nominatim
from odoo import http
from odoo.http import request


class PackersAndMoversManagementController(http.Controller):
    """Class to add truck booking menu in website"""

    @http.route('/booking', auth='public', website=True)
    def truck_booking(self):
        """Function to render truck booking values to XML"""
        truck_ids = request.env['fleet.vehicle.model'].sudo().search([('vehicle_type', '=', 'truck')])
        goods_ids = request.env['goods.type'].sudo().search([])
        state_ids = request.env['res.country.state'].sudo().search([])
        country_ids = request.env['res.country'].sudo().search([])
        return http.request.render('packers_and_movers_management.truck_booking_page',
                                   {'truck_ids': truck_ids,
                                    'goods_ids': goods_ids,
                                    'state_ids': state_ids,
                                    'country_ids': country_ids})

    @http.route('/booking/submit', type='http', auth='public', website=True)
    def booking_success_page(self, **post):
        """Function to create booking and return to success page"""
        partner_id = request.env['res.partner'].sudo().create({
            'name': post.get('name'),
            'mobile': post.get('mobile_no'),
            'city': post.get('city'),
            'state_id': post.get('state'),
            'country_id': post.get('country')
        })
        booking_id = request.env['truck.booking'].sudo().create({
            'partner_id': partner_id.id,
            'from_location': post.get('pickup_location'),
            'to_location': post.get('drop_location'),
            'truck_id': post.get('truck_type'),
            'date': post.get('date'),
            'goods_type_id': post.get('goods_type'),
            'weight': post.get('weight'),
            'unit': post.get('unit')
        })
        return request.render('packers_and_movers_management.truck_booking_success_page',
                              {'partner_id': partner_id,
                               'booking_id': booking_id})

    @http.route('/goods', type='http', auth='public', website=True)
    def goods_type(self):
        """Function to return values to xml"""
        goods_ids = request.env['goods.type'].sudo().search([])
        return http.request.render('packers_and_movers_management.goods_page',
                                   {'goods_ids': goods_ids})

    @http.route('/truck', type='http', auth='public', website=True)
    def truck_details(self):
        """Function to render values to XML"""
        truck_type_ids = request.env['truck.type'].sudo().search([])
        return http.request.render('packers_and_movers_management.truck_page',
                                   {'truck_type_ids': truck_type_ids})

    @http.route(['/geo/<from_location>/<to_location>'], type='json', auth="none", website=False, csrf=False)
    def geo_location(self, from_location, to_location):
        """Function to Calculate distance between from and to location"""
        locator = Nominatim(user_agent="my_distance_app")
        from_location = locator.geocode(from_location)
        to_location = locator.geocode(to_location)
        from_lat = radians(from_location.latitude)
        from_long = radians(from_location.longitude)
        to_lat = radians(to_location.latitude)
        to_long = radians(to_location.longitude)
        dist_long = to_long - from_long
        dist_lat = to_lat - from_lat
        comp = sin(dist_lat / 2) ** 2 + cos(from_lat) * cos(to_lat) * sin(
            dist_long / 2) ** 2
        return int(2 * asin(sqrt(comp)) * 6371)
