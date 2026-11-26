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

from odoo import models, fields, api


class TraccarTrip(models.Model):
    """
    Represents a single trip fetched from Traccar /api/reports/trips.
    """
    _name = 'fleet.traccar.trip'
    _description = 'Traccar Trip'
    _order = 'start_time desc'
    _rec_name = 'display_name'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, index=True, ondelete='cascade')
    device_id = fields.Many2one('fleet.traccar.device', string='Device', ondelete='set null')

    start_time = fields.Datetime(string='Start Time')
    end_time = fields.Datetime(string='End Time')
    duration = fields.Float(string='Duration (min)', compute='_compute_duration', store=True)

    start_address = fields.Char(string='Start Address')
    end_address = fields.Char(string='End Address')
    start_lat = fields.Float(string='Start Latitude', digits=(10, 7))
    start_lng = fields.Float(string='Start Longitude', digits=(10, 7))
    end_lat = fields.Float(string='End Latitude', digits=(10, 7))
    end_lng = fields.Float(string='End Longitude', digits=(10, 7))

    distance = fields.Float(string='Distance (km)')
    avg_speed = fields.Float(string='Avg Speed (km/h)')
    max_speed = fields.Float(string='Max Speed (km/h)')

    position_ids = fields.One2many('fleet.traccar.position', 'trip_id', string='Positions')
    position_count = fields.Integer(compute='_compute_position_count', string='Points')

    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        """Compute trip duration in minutes from start and end time."""
        for rec in self:
            if rec.start_time and rec.end_time:
                delta = rec.end_time - rec.start_time
                rec.duration = delta.total_seconds() / 60.0
            else:
                rec.duration = 0.0

    @api.depends('position_ids')
    def _compute_position_count(self):
        """Compute the total number of positions recorded for this trip."""
        for rec in self:
            rec.position_count = len(rec.position_ids)

    @api.depends('vehicle_id', 'start_time')
    def _compute_display_name(self):
        """Compute a display name combining vehicle name and trip start time."""
        for rec in self:
            vehicle = rec.vehicle_id.name if rec.vehicle_id else 'Unknown'
            time_str = rec.start_time.strftime('%Y-%m-%d %H:%M') if rec.start_time else ''
            rec.display_name = f'{vehicle} – {time_str}'
