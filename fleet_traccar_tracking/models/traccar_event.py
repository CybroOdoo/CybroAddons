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


class TraccarEvent(models.Model):
    """
    Stores device events forwarded by Traccar (overspeed, geofence, alarm, etc.).
    """
    _name = 'fleet.traccar.event'
    _description = 'Traccar Event'
    _order = 'event_time desc'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', compute='_compute_name', store=True)

    @api.depends('event_type', 'event_time')
    def _compute_name(self):
        for record in self:
            event_str = dict(self._fields['event_type'].selection).get(record.event_type, record.event_type)
            time_str = record.event_time.strftime('%Y-%m-%d %H:%M') if record.event_time else 'Unknown Time'
            record.name = f"{event_str} ({time_str})"


    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', index=True, ondelete='cascade')
    device_id = fields.Many2one('fleet.traccar.device', string='Device', ondelete='set null')
    position_id = fields.Many2one('fleet.traccar.position', string='Position', ondelete='set null')

    traccar_event_id = fields.Integer(string='Traccar Event ID', index=True)
    event_time = fields.Datetime(string='Event Time', required=True)

    event_type = fields.Selection([
        ('deviceOnline', 'Device Online'),
        ('deviceOffline', 'Device Offline'),
        ('deviceUnknown', 'Device Unknown'),
        ('deviceMoving', 'Device Moving'),
        ('deviceStopped', 'Device Stopped'),
        ('deviceOverspeed', 'Overspeed'),
        ('geofenceEnter', 'Geofence Enter'),
        ('geofenceExit', 'Geofence Exit'),
        ('alarm', 'Alarm'),
        ('ignitionOn', 'Ignition On'),
        ('ignitionOff', 'Ignition Off'),
        ('other', 'Other'),
    ], string='Event Type', default='other', tracking=True)

    geofence_id = fields.Integer(string='Geofence ID')
    attributes = fields.Json(string='Raw Attributes')
    notes = fields.Char(string='Notes')
