# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from math import asin, cos, sin, radians, sqrt
from geopy import Nominatim
from odoo import http
from odoo.http import request


class PackersAndMoversManagementController(http.Controller):
    """Class to add truck booking menu in website"""

    @http.route('/booking', auth='public', website=True)
    def truck_booking(self):
        """Function to render truck booking values to XML"""
        truck_ids = request.env['fleet.vehicle.model'].sudo().search(
            [('vehicle_type', '=', 'truck')])
        if not truck_ids:
            truck_ids = request.env['fleet.vehicle.model'].sudo().search([])
        goods_ids = request.env['goods.type'].sudo().search([])
        country_ids = request.env['res.country'].sudo().search([])
        state_ids = request.env['res.country.state'].sudo().search(
            [('country_id', 'in', country_ids.ids)])
        return http.request.render(
            'packers_and_movers_management.truck_booking_page',
            {'truck_ids': truck_ids,
             'goods_ids': goods_ids,
             'state_ids': state_ids,
             'country_ids': country_ids})

    @http.route('/booking/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def booking_success_page(self, **post):
        """Function to create booking and return to success page"""
        state_id = int(post['state']) if post.get('state') and post['state'].isdigit() else False
        country_id = int(post['country']) if post.get('country') and post['country'].isdigit() else False
        partner_id = request.env['res.partner'].sudo().create({
            'name': post.get('name'),
            'city': post.get('city'),
            'state_id': state_id,
            'country_id': country_id,
        })
        truck_id = int(post['truck_type']) if post.get('truck_type') and post['truck_type'].isdigit() else False
        goods_type_id = int(post['goods_type']) if post.get('goods_type') and post['goods_type'].isdigit() else False
        distance = float(post['distance']) if post.get('distance') else 0.0
        weight = int(post['weight']) if post.get('weight') and post['weight'].isdigit() else 0
        booking_id = request.env['truck.booking'].sudo().create({
            'partner_id': partner_id.id,
            'from_location': post.get('pickup_location'),
            'to_location': post.get('drop_location'),
            'distance': distance,
            'truck_id': truck_id,
            'date': post.get('date'),
            'goods_type_id': goods_type_id,
            'weight': weight,
            'unit': post.get('unit'),
        })
        return request.render(
            'packers_and_movers_management.truck_booking_success_page',
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

    @http.route(['/geo/<from_location>/<to_location>'], type='jsonrpc',
                auth="none", website=False, csrf=False)
    def geo_location(self, from_location, to_location):
        """Function to Calculate distance between from and to location"""
        if not from_location or not to_location:
            return 0
        try:
            locator = Nominatim(user_agent="my_distance_app", timeout=10)
            from_loc = locator.geocode(from_location)
            to_loc = locator.geocode(to_location)
            if not from_loc or not to_loc:
                return 0
            from_lat = radians(from_loc.latitude)
            from_long = radians(from_loc.longitude)
            to_lat = radians(to_loc.latitude)
            to_long = radians(to_loc.longitude)
            dist_long = to_long - from_long
            dist_lat = to_lat - from_lat
            comp = sin(dist_lat / 2) ** 2 + cos(from_lat) * cos(to_lat) * sin(
                dist_long / 2) ** 2
            return int(2 * asin(sqrt(comp)) * 6371)
        except Exception:
            return 0
