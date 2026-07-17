# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta
import pytz


class CalendarEvent(models.Model):
    """Extends the calendar.event model to handle restaurant table reservations."""
    _inherit = 'calendar.event'

    is_restaurant_reservation = fields.Boolean(
        string="Is Restaurant Reservation",
        default=False,
        help="Check this if the calendar event is for a restaurant table reservation."
    )
    party_size = fields.Integer(
        string="Party Size",
        default=1,
        help="The number of guests for the reservation."
    )
    guest_name = fields.Char(
        string="Guest Name",
        help="Name of the guest making the reservation."
    )
    guest_phone = fields.Char(
        string="Guest Phone",
        help="Contact phone number of the guest."
    )
    guest_email = fields.Char(
        string="Guest Email",
        help="Contact email address of the guest."
    )

    @api.onchange('is_restaurant_reservation', 'guest_name', 'party_size')
    def _onchange_restaurant_reservation(self):
        """Updates the event name based on guest details for restaurant reservations."""
        for rec in self:
            if rec.is_restaurant_reservation:
                name = rec.guest_name or 'Guest'
                rec.name = f"Table Reservation: {name} ({rec.party_size} guests)"

    @api.onchange('start', 'is_restaurant_reservation')
    def _onchange_start_set_stop(self):
        """Sets the default duration of 30 minutes for restaurant reservations."""
        for rec in self:
            if rec.is_restaurant_reservation and rec.start:
                rec.stop = rec.start + timedelta(minutes=30)
                if hasattr(rec, 'duration'):
                    rec.duration = 0.5

    @api.constrains('start', 'stop', 'is_restaurant_reservation', 'active')
    def _check_reservation_overlap(self):
        """Ensures that restaurant reservations do not overlap with existing ones."""
        for rec in self:
            if rec.is_restaurant_reservation and rec.start and rec.stop and rec.active:
                domain = [
                    ('active', '=', True),
                    ('id', '!=', rec.id),
                    '|',
                    ('name', '=like', 'Table Reservation:%'),
                    ('is_restaurant_reservation', '=', True),
                    ('start', '<', rec.stop),
                    ('stop', '>', rec.start),
                ]
                overlapping = self.search(domain, limit=1)
                if overlapping:
                    raise ValidationError(
                        f"The selected time slot is already reserved by another guest ({overlapping.name}). Please choose another time.")

    @api.constrains('start', 'is_restaurant_reservation')
    def _check_time_slot_range(self):
        """Restricts restaurant reservations to the allowed evening time slots."""
        for rec in self:
            if rec.is_restaurant_reservation and rec.start:
                tz_name = self.env.context.get('tz') or self.env.user.tz or 'UTC'
                user_tz = pytz.timezone(tz_name)
                local_start = pytz.utc.localize(rec.start).astimezone(user_tz)

                start_time = float(self.env['ir.config_parameter'].sudo().get_param('restaurant.reservation_start_time',
                                                                                    default='17.0'))
                end_time = float(
                    self.env['ir.config_parameter'].sudo().get_param('restaurant.reservation_end_time', default='23.0'))

                local_start_float = local_start.hour + local_start.minute / 60.0

                if local_start_float < start_time or local_start_float >= end_time:
                    def format_time(t):
                        h = int(t)
                        m = int(round((t - h) * 60))
                        am_pm = 'AM' if h < 12 else 'PM'
                        h_12 = h if h <= 12 else h - 12
                        h_12 = 12 if h_12 == 0 else h_12
                        return f"{h_12}:{m:02d} {am_pm}"

                    raise ValidationError(
                        f"Reservations can only be made between {format_time(start_time)} and {format_time(end_time)}.")
