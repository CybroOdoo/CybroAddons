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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""
This module defines the controllers for the DriveX theme.
"""
import datetime
import urllib.parse
from odoo import http
from odoo.http import request


class DriveXController(http.Controller):
    """DriveX website controllers."""

    @http.route('/fleet', type='http', auth='public', website=True, sitemap=True)
    def drivex_fleet(self, **kwargs):
        """Render the fleet page with search filters."""
        domain = [('is_available_on_website', '=', True)]
        pickup_date = kwargs.get('pickup_date')
        pickup_time = kwargs.get('pickup_time', '12:00 PM')
        return_date = kwargs.get('return_date')
        return_time = kwargs.get('return_time', '12:00 PM')
        category = kwargs.get('category')
        pickup_loc = kwargs.get('pickup_loc')
        if category and category != 'all':
            domain.append(('category_id.name', '=ilike', category))
        if pickup_date and return_date:
            try:
                pickup_dt_str = f"{pickup_date} {pickup_time}"
                return_dt_str = f"{return_date} {return_time}"
                pickup_dt = datetime.datetime.strptime(pickup_dt_str, '%Y-%m-%d %I:%M %p')
                return_dt = datetime.datetime.strptime(return_dt_str, '%Y-%m-%d %I:%M %p')
                # Find overlapping bookings
                overlapping_orders = request.env['fleet.rental.order'].sudo().search([
                    ('state', 'in', ['confirmed', 'picked_up']),
                    ('pickup_datetime', '<', return_dt),
                    ('return_datetime', '>', pickup_dt),
                ])
                booked_vehicle_ids = overlapping_orders.mapped('vehicle_id.id')
                if booked_vehicle_ids:
                    domain.append(('id', 'not in', booked_vehicle_ids))
            except Exception as e:
                # If date parsing fails, proceed without filtering by date
                pass
        has_vehicles = request.env['fleet.vehicle'].sudo().search_count([('is_available_on_website', '=', True)]) > 0
        vehicles = request.env['fleet.vehicle'].sudo().search(domain)
        categories = request.env['fleet.vehicle.model.category'].sudo().search([])
        qs_params = {}
        if pickup_date: qs_params['pickup_date'] = pickup_date
        if pickup_time: qs_params['pickup_time'] = pickup_time
        if return_date: qs_params['return_date'] = return_date
        if return_time: qs_params['return_time'] = return_time
        if pickup_loc: qs_params['pickup_loc'] = pickup_loc
        query_string = f"?{urllib.parse.urlencode(qs_params)}" if qs_params else ""
        return request.render('theme_drivex.drivex_fleet_page', {
            'vehicles': vehicles,
            'categories': categories,
            'search_params': {
                'pickup_date': pickup_date,
                'pickup_time': pickup_time,
                'return_date': return_date,
                'return_time': return_time,
                'category': category,
                'pickup_loc': pickup_loc,
            },
            'query_string': query_string,
            'demo_fallback': not has_vehicles,
        })

    @http.route('/services', type='http', auth='public', website=True, sitemap=True)
    def drivex_services(self, **kwargs):
        """Render the services page."""
        return request.render('theme_drivex.drivex_services_page')

    @http.route('/about', type='http', auth='public', website=True, sitemap=True)
    def drivex_about(self, **kwargs):
        """Render the about page."""
        return request.render('theme_drivex.drivex_about_page')

    @http.route('/contact', type='http', auth='public', website=True, sitemap=True)
    def drivex_contact(self, **kwargs):
        """Render the contact page."""
        return request.render('theme_drivex.drivex_contact_page')

    @http.route(['/booking', '/booking/<int:vehicle_id>'], type='http', auth='public', website=True)
    def drivex_booking(self, vehicle_id=None, **kwargs):
        """Render the booking wizard page."""
        vehicle = request.env['fleet.vehicle'].sudo().browse(vehicle_id) if vehicle_id else None
        has_vehicles = request.env['fleet.vehicle'].sudo().search_count([('is_available_on_website', '=', True)]) > 0
        if (not vehicle or not vehicle.exists()) and has_vehicles:
            return request.redirect('/fleet')
        locations = request.env['fleet.rental.location'].sudo().search([('active', '=', True)])
        insurances = request.env['fleet.rental.insurance'].sudo().search([('active', '=', True)])
        addons = request.env['fleet.rental.addon'].sudo().search([('active', '=', True)])
        return request.render('theme_drivex.drivex_booking_page', {
            'vehicle': vehicle,
            'locations': locations,
            'insurances': insurances,
            'addons': addons,
            'demo_fallback': not has_vehicles,
        })

    @http.route(['/car-detail', '/car-detail/<int:vehicle_id>'], type='http', auth='public', website=True)
    def drivex_car_detail(self, vehicle_id=None, **kwargs):
        """Render the car detail page."""
        vehicle = request.env['fleet.vehicle'].sudo().browse(vehicle_id) if vehicle_id else None
        has_vehicles = request.env['fleet.vehicle'].sudo().search_count([('is_available_on_website', '=', True)]) > 0
        if (not vehicle or not vehicle.exists()) and has_vehicles:
            return request.redirect('/fleet')
        qs_params = {k: v for k, v in kwargs.items() if v}
        query_string = f"?{urllib.parse.urlencode(qs_params)}" if qs_params else ""
        locations = request.env['fleet.rental.location'].sudo().search([('active', '=', True)])
        insurances = request.env['fleet.rental.insurance'].sudo().search([('active', '=', True)])
        return request.render('theme_drivex.drivex_car_detail_page', {
            'vehicle': vehicle,
            'locations': locations,
            'insurances': insurances,
            'query_string': query_string,
            'demo_fallback': not has_vehicles,
        })

    @http.route('/booking/submit', type='json', auth='public', website=True)
    def drivex_booking_submit(self, **post):
        """Submit the booking form."""
        vehicle_id = post.get('vehicle_id')
        pickup_date = post.get('pickup_date')
        return_date = post.get('return_date')
        pickup_time = post.get('pickup_time', '12:00 PM')
        return_time = post.get('return_time', '12:00 PM')
        pickup_loc_id = post.get('pickup_location_id')
        return_loc_id = post.get('return_location_id')
        driver_fname = post.get('driver_fname')
        driver_lname = post.get('driver_lname')
        driver_email = post.get('driver_email')
        driver_phone = post.get('driver_phone')
        driver_license = post.get('driver_license')
        insurance_id = post.get('insurance_id')
        addon_ids = post.get('addon_ids', [])
        if not all([vehicle_id, pickup_date, return_date, pickup_loc_id]):
            return {'error': 'Missing required fields.'}
        try:
            if str(vehicle_id) == '0':
                import random
                import string
                ref = 'DRX-DEMO-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                return {'success': True, 'order_id': 0, 'order_name': ref}
            # Parse dates and times
            pickup_dt_str = f"{pickup_date} {pickup_time}"
            return_dt_str = f"{return_date} {return_time}"
            pickup_dt = datetime.datetime.strptime(pickup_dt_str, '%Y-%m-%d %I:%M %p')
            return_dt = datetime.datetime.strptime(return_dt_str, '%Y-%m-%d %I:%M %p')
            # Compute days securely
            delta = return_dt - pickup_dt
            days = max(1, (delta.days + (1 if delta.seconds > 0 else 0)))
            vehicle = request.env['fleet.vehicle'].sudo().browse(int(vehicle_id))
            base_amount = vehicle.daily_rate * days
            insurance_amount = 0.0
            if insurance_id:
                ins = request.env['fleet.rental.insurance'].sudo().browse(int(insurance_id))
                insurance_amount = ins.price_per_day * days
            addons_amount = 0.0
            for addon_id in addon_ids:
                add = request.env['fleet.rental.addon'].sudo().browse(int(addon_id))
                if add.charge_type == 'per_day':
                    addons_amount += (add.price * days)
                else:
                    addons_amount += add.price
            # Create Order
            order_vals = {
                'vehicle_id': vehicle.id,
                'pickup_datetime': pickup_dt,
                'return_datetime': return_dt,
                'pickup_location_id': int(pickup_loc_id),
                'return_location_id': int(return_loc_id) if return_loc_id and return_loc_id != 'same' else int(pickup_loc_id),
                'driver_name': f"{driver_fname} {driver_lname}",
                'driver_email': driver_email,
                'driver_phone': driver_phone,
                'driver_license': driver_license,
                'insurance_id': int(insurance_id) if insurance_id else False,
                'addon_ids': [(6, 0, [int(x) for x in addon_ids])],
                'amount_base': base_amount,
                'amount_insurance': insurance_amount,
                'amount_addons': addons_amount,
                'state': 'confirmed',
            }
            order = request.env['fleet.rental.order'].sudo().create(order_vals)
            # Send Confirmation Email
            template = request.env.ref('theme_drivex.email_template_rental_booking_confirmation', raise_if_not_found=False)
            if template:
                template.sudo().send_mail(order.id, force_send=True)
            return {'success': True, 'order_id': order.id, 'order_name': order.name}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/vehicle/<int:vehicle_id>/booked-dates', type='json', auth='public', website=True)
    def drivex_vehicle_booked_dates(self, vehicle_id, **kwargs):
        """Return confirmed/picked_up booking date ranges for the given vehicle.
        Returns a list of {from: 'YYYY-MM-DD', to: 'YYYY-MM-DD'} objects so
        the frontend date picker can disable those days.
        """
        orders = request.env['fleet.rental.order'].sudo().search([
            ('vehicle_id', '=', vehicle_id),
            ('state', 'in', ['confirmed', 'picked_up']),
        ])
        ranges = []
        for order in orders:
            if order.pickup_datetime and order.return_datetime:
                ranges.append({
                    'from': order.pickup_datetime.strftime('%Y-%m-%d'),
                    'to': order.return_datetime.strftime('%Y-%m-%d'),
                })
        return {'ranges': ranges}
