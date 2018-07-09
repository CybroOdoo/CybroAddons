# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Avinash Nk(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import json
from datetime import datetime, date
from odoo import http
from odoo.http import request


class SalonBookingWeb(http.Controller):

    @http.route('/page/salon_details', csrf=False, type="http", methods=['POST', 'GET'], auth="public", website=True)
    def salon_details(self, **kwargs):

        name = kwargs['name']
        date = kwargs['date']
        time = kwargs['time']
        phone = kwargs['phone']
        email = kwargs['email']
        chair = kwargs['chair']
        j = 0
        service_list = []
        while(j < (int(kwargs['number']))):
            item = "list_service["+str(j)+"][i]"
            service_list.append(int(kwargs[item]))
            j += 1
        salon_service_obj = request.env['salon.service'].search([('id', 'in', service_list)])
        dates_time = date+" "+time+":00"
        date_and_time = datetime.strptime(dates_time, '%m/%d/%Y %H:%M:%S')
        salon_booking = request.env['salon.booking']
        booking_data = {
            'name': name,
            'phone': phone,
            'time': date_and_time,
            'email': email,
            'chair_id': chair,
            'services': [(6, 0, [x.id for x in salon_service_obj])],
        }
        salon_booking.create(booking_data)
        return json.dumps({'result': True})

    @http.route('/page/salon_check_date', type='json', auth="public", website=True)
    def salon_check(self, **kwargs):
        date_info = kwargs.get('check_date')
        return date_info

    @http.route('/page/salon_management.salon_booking_thank_you', type='http', auth="public", website=True)
    def thank_you(self, **post):
        return request.render('salon_management.salon_booking_thank_you', {})

    @http.route('/page/salon_management.salon_booking_form', type='http', auth="public", website=True)
    def chair_info(self, **post):

        salon_service_obj = request.env['salon.service'].search([])
        salon_working_hours_obj = request.env['salon.working.hours'].search([])
        salon_holiday_obj = request.env['salon.holiday'].search([('holiday', '=', True)])
        date_check = date.today()
        if 'x' in post.keys():
            date_check = post['x']
        chair_obj = request.env['salon.chair'].search([('active_booking_chairs', '=', True)])
        order_obj = request.env['salon.order'].search([('chair_id.active_booking_chairs', '=', True),
                                                       ('stage_id', 'in', [1, 2, 3])])
        date_check = str(date_check)
        order_obj = order_obj.search([('start_date_only', '=', date_check)])
        return request.render('salon_management.salon_booking_form',
                                      {'chair_details': chair_obj, 'order_details': order_obj,
                                       'salon_services': salon_service_obj, 'date_search': date_check,
                                       'holiday': salon_holiday_obj,
                                       'working_time': salon_working_hours_obj})