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
from odoo import fields, models


class FlightEvent(models.Model):
    """Store flight event records."""
    _name = 'flight.event'
    _description = 'Flight Event'
    _order = 'timestamp'

    flight_id = fields.Many2one('flight.flight', string='Flight', required=True, ondelete='cascade', help='Flight associated with this event')
    event_type = fields.Selection(
        [
            ('takeoff', 'Takeoff'),
            ('landing', 'Landing'),
            ('gate_out', 'Gate Out'),
            ('gate_in', 'Gate In'),
            ('other', 'Other'),
        ],
        string='Event Type', required=True,
        help='Type of event occurring during the flight',
    )
    timestamp = fields.Datetime(string='Timestamp', required=True, help='Date and time when the event occurred')
    notes = fields.Char(string='Notes', help='Additional notes or remarks regarding the event')