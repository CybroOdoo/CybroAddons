# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
import json
import pytz
from datetime import datetime, time
from odoo import fields, http
from odoo.http import request


class SalonBookingWeb(http.Controller):
    """Route to do salon website operations."""

    @http.route(route='/page/salon_details', type='json', auth='public',
                website=True, csrf=False)
    def salon_details(self, name, date, salon_time, phone, email, chair,
                      number):
        val = 0
        service_list = []
        while val < (int(number)):
            service_list.append(int(val))
            val += 1
        dates_time = date + " " + salon_time + ":00"
        date_and_time = (pytz.timezone(request.env.user.tz).localize(
            datetime.strptime(str(dates_time), '%Y-%m-%d %H:%M:%S')).
                         astimezone(pytz.UTC).replace(tzinfo=None))
        a = request.env['salon.booking'].create({
            'name': name,
            'phone': phone,
            'time': date_and_time,
            'email': email,
            'chair_id': chair,
            'service_ids': [(6, 0, [salon.id for salon in request.env
                                    ['salon.service'].search([('id', 'in',
                                                             service_list)])])],
        })
        return json.dumps({'result': True})

    @http.route('/page/salon_check_date', type='json', auth="public",
                website=True)
    def salon_check(self, **kwargs):
        year, month, day = map(int, kwargs['check_date'].split('-'))
        date_start = pytz.timezone(request.env.user.tz).localize(
            datetime(year, month, day, hour=0, minute=0, second=0)).astimezone(
            pytz.UTC).replace(tzinfo=None)
        date_end = (pytz.timezone(request.env.user.tz).
                    localize(datetime(year, month, day, hour=23, minute=59,
                                      second=59)).astimezone(pytz.UTC).
                    replace(tzinfo=None))
        order_obj = request.env['salon.order'].search(
            [('chair_id.active_booking_chairs', '=', True),
             ('stage_id', 'in', [1, 2, 3]), ('start_time', '>=', date_start),
             ('start_time', '<=', date_end)])
        order_details = {}
        for order in order_obj:
            data = {
                'number': order.id,
                'start_time_only': fields.Datetime.to_string(pytz.UTC.localize(
                    order.start_time).astimezone(pytz.timezone(
                                    request.env.user.tz)).replace(tzinfo=None))[11:16],
                'end_time_only': fields.Datetime.to_string(pytz.UTC.localize(
                    order.end_time).astimezone(pytz.timezone(
                                    request.env.user.tz)).replace(tzinfo=None))[11:16],
            }
            if order.chair_id.id not in order_details:
                order_details[order.chair_id.id] = {
                    'name': order.chair_id.name,
                    'orders': [data],
                }
            else:
                order_details[order.chair_id.id]['orders'].append(data)
        return order_details

    @http.route('/page/salon_management/salon_booking_thank_you',
                type='http', auth="public", website=True, csrf=False)
    def return_thank_you(self, **post):
        return request.render('salon_management.salon_booking_thank_you', {})

    @http.route('/salon_booking_form', type='http',
                auth="public", website=True)
    def chair_info(self, **post):
        """Route function that render while clicking Booking menu from website.
           Returns data to booking website"""
        salon_service_obj = request.env['salon.service'].search([])
        salon_working_hours_obj = request.env['salon.working.hours'].search([])
        salon_holiday_obj = request.env['salon.holiday'].search(
            [('holiday', '=', True)])
        date_check = datetime.today().date()
        date_start = (pytz.timezone(request.env.user.tz).localize(
            datetime.combine(date_check, time(hour=0, minute=0, second=0))).
                      astimezone(pytz.UTC).replace(tzinfo=None))
        date_end = (pytz.timezone(request.env.user.tz).localize(
            datetime.combine(date_check, time(hour=23, minute=59, second=59))).
                    astimezone(pytz.UTC).replace(tzinfo=None))
        # chair_obj =
        order_obj = request.env['salon.order'].search(
            [('chair_id.active_booking_chairs', '=', True),
             ('stage_id', 'in', [1, 2, 3]), ('start_time', '>=', date_start),
             ('start_time', '<=', date_end)])
        return request.render(
            'salon_management.salon_booking_form', {
                'chair_details': request.env['salon.chair'].search([]),
                'order_details': order_obj,
                'salon_services': salon_service_obj,
                'date_search': date_check,
                'holiday': salon_holiday_obj,
                'working_time': salon_working_hours_obj}
        )


class SalonOrders(http.Controller):
    """Returns the chairs for dashboard"""

    @http.route(route='/salon/chairs', type="json", auth="public")
    def get_salon_chair(self, products_per_slide=3):
        """Function to returns the chairs for dashboard"""
        chairs = []
        number_of_orders = {}
        for chair in request.env['salon.chair'].sudo().search([]):
            number_of_orders.update({
                chair.id: len(request.env['salon.order'].search(
                    [("chair_id", "=", chair.id),
                     ("stage_id", "in", [2, 3])]))})
            chairs.append({'name': chair.name,
                           'id': chair.id,
                           'orders': number_of_orders[chair.id]})
        return chairs
