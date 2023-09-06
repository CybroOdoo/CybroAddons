# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Risvana AR (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models
from odoo.exceptions import ValidationError


class VenueAvailable(models.TransientModel):
    """Model for managing the Venue availability information"""
    _name = 'check.venue.availability'
    _description = 'Venue Availability'

    booking_type = fields.Selection([('day', 'Day'),
                                     ('hour', 'Hours')], string='Booking Type',
                                    default='day',
                                    help='The selection field for Booking Type')
    venue_id = fields.Many2one('venue', string='Venue',
                               help='You can choose the Venue', required=True)
    start_date = fields.Datetime(string="Start date",
                                 default=lambda self: fields.datetime.now(),
                                 required=True,
                                 help='Venue Booking Start Date')
    end_date = fields.Datetime(string="End date", required=True,
                               help='Venue Booking End Date')
    budget = fields.Float(string="Booking Amount Budget", help='We can check the budget amount')
    capacity = fields.Float(string="Capacity", help='Venue capacity for the Booking')

    def action_search_venue(self):
        """"The button to search for bookings and check the bookings availability"""
        booking = self.env['venue.booking'].search([
            ('venue_id', '=', self.venue_id.id),
            ('start_date', '<', self.end_date),
            ('end_date', '>', self.start_date),
        ])
        if booking:
            raise ValidationError(
                "Venue is not available for the selected time range.")
        venue = self.env['venue'].browse(int(self.venue_id.id))
        if venue and venue.capacity <= self.capacity:
            raise ValidationError(
                "Venue is not available for the specified capacity.")
        budget_limit_exceeded = False
        if self.booking_type == 'day':
            budget_limit_exceeded = self.venue_id.venue_charge_day + self.venue_id.additional_charge_day > self.budget
        elif self.booking_type == 'hour':
            budget_limit_exceeded = self.venue_id.venue_charge_hour + self.venue_id.additional_charge_hour > self.budget
        if self.budget and budget_limit_exceeded:
            raise ValidationError(
                "Venue is not available for the specified Budget.")
        else:
            view_id = self.env.ref(
                'venue_booking_management.venue_booking_view_form').id
            return {
            'type': 'ir.actions.act_window',
            'name': 'Venue Booking',
            'view_mode': 'form',
            'res_model': 'venue.booking',
            'target': 'current',
            'context': {
                'create': True,
                'default_venue_id': self.venue_id.id,
                'default_booking_type': self.booking_type,
                'default_end_date': self.end_date,
                'default_start_date': self.start_date,
            },
            'views': [[view_id, 'form']],
        }
