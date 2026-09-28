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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FlightFlight(models.Model):
    """Manage flight operations."""
    _name = 'flight.flight'
    _description = 'Flight'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_departure desc'

    name = fields.Char(
        string='Flight Number', required=True, copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('flight.flight') or 'New',
        help='Unique flight code or flight number',
    )
    aircraft_id = fields.Many2one(
        'flight.aircraft', string='Aircraft', tracking=True,
        domain="[('status', '=', 'active')]",
        help='Aircraft assigned to perform this flight',
    )
    origin_id = fields.Many2one('flight.aerodrome', string='Origin', required=True, help='Origin aerodrome for the flight')
    destination_id = fields.Many2one('flight.aerodrome', string='Destination', required=True, help='Destination aerodrome for the flight')
    scheduled_departure = fields.Datetime(string='Scheduled Departure', required=True, tracking=True, help='Scheduled date and time of departure')
    scheduled_arrival = fields.Datetime(string='Scheduled Arrival', required=True, help='Scheduled date and time of arrival')
    actual_departure = fields.Datetime(string='Actual Departure', copy=False, help='Actual date and time of departure')
    actual_arrival = fields.Datetime(string='Actual Arrival', copy=False, help='Actual date and time of arrival')
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('dispatched', 'Dispatched'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status', default='draft', required=True, tracking=True, copy=False,
        help='Current operational state of the flight',
    )
    event_ids = fields.One2many('flight.event', 'flight_id', string='Flight Events', help='Events recorded for this flight')
    active = fields.Boolean(default=True, help='Set active to false to hide this flight record')

    @api.constrains('origin_id', 'destination_id')
    def _check_origin_destination(self):
        """Ensure origin and destination are different."""
        for flight in self:
            if flight.origin_id and flight.destination_id and flight.origin_id == flight.destination_id:
                raise ValidationError("Origin and destination aerodromes must be different.")

    @api.constrains('scheduled_departure', 'scheduled_arrival')
    def _check_scheduled_times(self):
        """Ensure the arrival is after the departure."""
        for flight in self:
            if flight.scheduled_departure and flight.scheduled_arrival:
                if flight.scheduled_arrival <= flight.scheduled_departure:
                    raise ValidationError("Scheduled arrival must be after scheduled departure.")

    def action_confirm_schedule(self):
        """Schedule draft flights."""
        for flight in self:
            if flight.state != 'draft':
                raise ValidationError("Only draft flights can be scheduled.")
            if not flight.aircraft_id:
                raise ValidationError("An aircraft must be assigned before scheduling.")
        self.write({'state': 'scheduled'})

    def action_dispatch(self):
        """Dispatch scheduled flights."""
        for flight in self:
            if flight.state != 'scheduled':
                raise ValidationError("Only scheduled flights can be dispatched.")
            if flight.aircraft_id.status != 'active':
                raise ValidationError(
                    "Aircraft %s is not active (status: %s) and cannot be dispatched."
                    % (flight.aircraft_id.name, flight.aircraft_id.status)
                )
        self.write({'state': 'dispatched'})

    def action_start(self):
        """Start dispatched flights."""
        for flight in self:
            if flight.state != 'dispatched':
                raise ValidationError("Only dispatched flights can move to in progress.")
        self.write({
            'state': 'in_progress',
            'actual_departure': fields.Datetime.now(),
        })

    def action_complete(self):
        """Complete in-progress flights."""
        for flight in self:
            if flight.state != 'in_progress':
                raise ValidationError("Only in-progress flights can be completed.")
        self.write({
            'state': 'completed',
            'actual_arrival': fields.Datetime.now(),
        })

    def action_cancel(self):
        """Cancel eligible flights."""
        for flight in self:
            if flight.state in ('completed', 'cancelled'):
                raise ValidationError("Completed or already cancelled flights cannot be cancelled.")
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        """Reset flights to draft."""
        self.write({'state': 'draft'})