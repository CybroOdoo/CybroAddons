# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
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
from openerp.addons.web import http
from openerp import models, fields, _, SUPERUSER_ID, api
from openerp.addons.web.http import request
from datetime import datetime, date


class SalonBookingBackend(models.Model):

    _name = 'salon.booking'

    name = fields.Char(string="Name")
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'), ('rejected', 'Rejected')], default="draft")
    time = fields.Datetime(string="Date")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="E-Mail")
    services = fields.Many2many('salon.service', string="Services")
    chair_id = fields.Many2one('salon.chair', string="Chair")
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company'].browse(1))
    lang = fields.Many2one('res.lang', 'Language',
                           default=lambda self: self.env['res.lang'].browse(1))

    def all_salon_orders(self):
        if self.time:
            date_only = str(self.time)[0:10]
        else:
            date_only = date.today()
        all_salon_service_obj = self.env['salon.order'].search([('chair_id', '=', self.chair_id.id),
                                                                ('start_date_only', '=', date_only)])
        self.filtered_orders = [(6, 0, [x.id for x in all_salon_service_obj])]

    filtered_orders = fields.Many2many('salon.order', string="Salon Orders", compute="all_salon_orders")

    @api.multi
    def booking_approve(self):
        salon_order_obj = self.env['salon.order']
        salon_service_obj = self.env['salon.order.lines']
        order_data ={
            'customer_name': self.name,
            'chair_id': self.chair_id.id,
            'start_time': self.time,
            'date': date.today(),
            'stage_id': 1,
            'booking_identifier': True,
        }
        order = salon_order_obj.create(order_data)
        for records in self.services:
            service_data = {
                'service_id': records.id,
                'time_taken': records.time_taken,
                'price': records.price,
                'price_subtotal': records.price,
                'salon_order': order.id,
            }
            salon_service_obj.create(service_data)
        template = self.env.ref('salon_management.salon_email_template_approved')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        self.state = "approved"

    @api.multi
    def booking_reject(self):
        template = self.env.ref('salon_management.salon_email_template_rejected')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        self.state = "rejected"


class SalonBookingWeb(http.Controller):

    @http.route('/page/salon_details', type='json', auth="public", website=True)
    def salon_details(self, **kwargs):
        booking_info = kwargs.get('salon_data')
        name = booking_info[0]
        date = booking_info[1]
        time = booking_info[2]
        phone = booking_info[3]
        email = booking_info[4]
        services = booking_info[5]
        chair = booking_info[6]
        salon_service_obj = request.env['salon.service'].search([('id', 'in', services)])
        dates_time = date+" "+time+":00"
        date_and_time = datetime.strptime(dates_time, '%m/%d/%Y %H:%M:%S')
        salon_booking = request.registry['salon.booking']
        booking_data = {
            'name': name,
            'phone': phone,
            'time': date_and_time,
            'email': email,
            'chair_id': chair,
            'services': [(6, 0, [x.id for x in salon_service_obj])],
        }
        salon_booking.create(request.cr, SUPERUSER_ID, booking_data, context=request.context)
        return

    @http.route('/page/salon_check_date', type='json', auth="public", website=True)
    def salon_check(self, **kwargs):
        date_info = kwargs.get('check_date')
        return date_info

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
        return request.website.render('salon_management.salon_booking_form',
                                      {'chair_details': chair_obj, 'order_details': order_obj,
                                       'salon_services': salon_service_obj, 'date_search': date_check,
                                       'holiday': salon_holiday_obj,
                                       'working_time': salon_working_hours_obj})