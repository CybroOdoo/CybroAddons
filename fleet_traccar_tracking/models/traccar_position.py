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

from odoo import models, fields


class TraccarPosition(models.Model):
    """
    Stores individual GPS fix records received from Traccar.
    Created by webhook or cron sync.
    """
    _name = 'fleet.traccar.position'
    _description = 'Traccar GPS Position'
    _order = 'fix_time desc'
    _rec_name = 'fix_time'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', index=True, ondelete='cascade')
    device_id = fields.Many2one('fleet.traccar.device', string='Device', index=True, ondelete='cascade')
    traccar_position_id = fields.Integer(string='Traccar Position ID', index=True)

    fix_time = fields.Datetime(string='Fix Time')
    server_time = fields.Datetime(string='Server Time')

    latitude = fields.Float(string='Latitude', digits=(10, 7))
    longitude = fields.Float(string='Longitude', digits=(10, 7))
    altitude = fields.Float(string='Altitude (m)')
    speed = fields.Float(string='Speed (km/h)')
    course = fields.Float(string='Course (°)')
    accuracy = fields.Float(string='Accuracy (m)')
    battery_level = fields.Float(string='Battery (%)')
    motion = fields.Boolean(string='Motion')
    odometer = fields.Float(string='Odometer (m)')

    attributes = fields.Json(string='Raw Attributes')

    trip_id = fields.Many2one('fleet.traccar.trip', string='Trip', ondelete='set null')
