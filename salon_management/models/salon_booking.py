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
import pytz
from odoo import fields, models
from datetime import datetime, time


class SalonBooking(models.Model):
    """Creates 'salon booking' to create salon bookings"""
    _name = 'salon.booking'
    _description = 'Salon Booking'

    name = fields.Char(string="Name", required=True, help="Name of customer")
    state = fields.Selection(string="State", default="draft",
                             selection=[('draft', 'Draft'),
                                        ('approved', 'Approved'),
                                        ('rejected', 'Rejected')],
                             help="State of the booking")
    time = fields.Datetime(string="Date", required=True,
                           help="Start time of the order")
    phone = fields.Char(string="Phone", help="Phone number of customer.")
    email = fields.Char(string="E-Mail", help="Email of employee")
    service_ids = fields.Many2many(comodel_name='salon.service',
                                   string="Services",
                                   help="Salon services")
    chair_id = fields.Many2one('salon.chair', string="Chair",
                               required=True, help="Select the chair for "
                                                   "booking")
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help="Default company")
    language_id = fields.Many2one(comodel_name='res.lang', string='Language',
                                  default=lambda self: self.env[
                                      'res.lang'].browse(1),
                                  help="Default language")
    filtered_order_ids = fields.Many2many(comodel_name='salon.order',
                                          string="Salon Orders",
                                          compute="_compute_filtered_order_ids",
                                          help="Orders for each salon")

    def _compute_filtered_order_ids(self):
        """Computes the filtered_order_ids field"""
        if self.time:
            date_only = fields.Date.to_date(fields.Datetime.to_string(
                pytz.UTC.localize(self.time).astimezone(pytz.timezone(
                    self.env.user.tz)))[0:10])
        else:
            date_only = fields.Date.context_today(self)
        date_start = (pytz.timezone(self.env.user.tz).localize(
            datetime.combine(date_only, time(hour=0, minute=0, second=0)))
                      .astimezone(pytz.UTC).replace(tzinfo=None))
        date_end = (pytz.timezone(self.env.user.tz).localize(
            datetime.combine(date_only, time(hour=23, minute=59, second=59)))
                    .astimezone(pytz.UTC).replace(tzinfo=None))
        salon_orders = self.env['salon.order'].search(
            [('chair_id', '=', self.chair_id.id),
             ('start_time', '>=', date_start),
             ('start_time', '<=', date_end)])
        self.filtered_order_ids = [(6, 0, [x.id for x in salon_orders])]

    def action_approve_booking(self):
        """Approve the booking for salon services"""
        for service in self.service_ids:
            self.env['salon.order.line'].create({
                'service_id': service.id,
                'time_taken': service.time_taken,
                'price': service.price,
                'price_subtotal': service.price,
                'salon_order_id': self.env['salon.order'].create(
                        {'customer_name': self.name,
                         'chair_id': self.chair_id.id,
                         'start_time': self.time,
                         'date': fields.Datetime.now(),
                         'stage_id': 1,
                         'booking_identifier': True}).id,
            })
        self.env['mail.template'].browse(self.env.ref(
            'salon_management.mail_template_salon_approved').id).send_mail(
                        self.id, force_send=True)
        self.state = "approved"

    def action_reject_booking(self):
        """Reject booking for salon services"""
        self.env['mail.template'].browse(self.env.ref(
            'salon_management.mail_template_salon_rejected')
                                         .id).send_mail(self.id,
                                                        force_send=True)
        self.state = "rejected"

    def get_booking_count(self):
        """Gets the count of salon bookings, recent works, salon orders, salon
            clients.
            Returns: Count of each one."""
        return {
            'bookings': self.env['salon.booking'].search_count(
                [('state', '=', 'approved')]),
            'sales': self.env['salon.order'].search_count(
                [('stage_id', 'in', [3, 4])]),
            'orders': self.env['salon.order'].search_count([]),
            'clients': self.env['res.partner'].search_count(
                [('partner_salon', '=', True)]),
            'chairs': self.env['salon.chair'].search([])
        }
