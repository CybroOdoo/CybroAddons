# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields, Command
import uuid


class AppointmentBooking(models.Model):
    """This model is used to store information for bookings"""
    _name = "appointment.booking"

    def _default_booking_token(self):
        """Used for the token generation"""
        return uuid.uuid4().hex

    account_move_id = fields.Many2one('account.move',
                                      help="Invoice linked with appointment")
    product_id = fields.Many2one('product.product', required=True,
                                 help="Booking product")
    staff_user_id = fields.Many2one('res.users', 'Operator', help="Staff user")
    name = fields.Char('Customer Name', help="Customer name")
    appointment_type_id = fields.Many2one('appointment.type',
                                          ondelete="cascade", required=True,
                                          help="Appointment related with "
                                               "booking")
    start = fields.Datetime('Start', required=True, help="Starting time")
    stop = fields.Datetime('Start', required=True, help="Ending Time")
    duration = fields.Float('Duration', help="Duration of the appointment")
    partner_id = fields.Many2one('res.partner', 'Contact', help="Customer")
    calender_event_id = fields.Many2one('calendar.event',
                                        help="Event created for booking")
    booking_line_ids = fields.One2many('appointment.booking.line',
                                       'calendar_booking_id',
                                       string="Booking Lines",
                                       help="Appointment booking lines")
    booking_token = fields.Char('Access Token', default=_default_booking_token,
                                readonly=True, help="To generate booking token")
    appointment_invite_id = fields.Many2one('appointment.invite',
                                            help="Appointment linked with "
                                                 "appointment invite")

    def make_invoice(self):
        """Create invoice when booking is created"""
        return self.env['account.move'].create([{
            'calendar_booking_ids': [Command.link(booking.id)],
            'invoice_line_ids': [Command.create({
                'display_type': 'product',
                'product_id': booking.product_id.id,
                'quantity': 1.0,
            })],
            'move_type': 'out_invoice',
            'partner_id': 1,
        } for booking in self])

    def make_event(self):
        """create event when invoice is created"""
        for booking in self:
            meeting = self.env['calendar.event'].sudo().create({
                'name': booking.appointment_type_id.name,
                'location': booking.appointment_type_id.location,
                'start': booking.start,
                'stop': booking.stop,
                'duration': booking.duration,
                'appointment_type_id': booking.appointment_type_id.id,
                'user_id': booking.staff_user_id.id,
            })
            booking.calender_event_id = meeting
