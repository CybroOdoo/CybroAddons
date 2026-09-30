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

import logging

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TraccarWebhook(http.Controller):

    @http.route(
        '/traccar/webhook/position',
        type='json',
        auth='public',
        csrf=False,
        methods=['POST'],
    )
    def traccar_position(self, **payload):
        """Receive a position update pushed by Traccar event forwarding."""
        device_id = payload.get('deviceId')
        latitude = payload.get('latitude')
        longitude = payload.get('longitude')
        speed = payload.get('speed', 0)
        fix_time = payload.get('fixTime')

        if not device_id:
            return {'status': 'error', 'message': 'No deviceId provided'}

        # Locate vehicle by linked traccar_device_id.traccar_id
        device = request.env['fleet.traccar.device'].sudo().search(
            [('traccar_id', '=', device_id)], limit=1
        )
        if device and device.vehicle_id:
            vehicle = device.vehicle_id
            vehicle._process_position({
                'deviceId': device_id,
                'latitude': latitude,
                'longitude': longitude,
                'speed': speed,
                'deviceTime': fix_time,
                'fixTime': fix_time,
            })
            _logger.info('Webhook: updated position for vehicle %s', vehicle.name)
        else:
            _logger.warning('Webhook: no vehicle found for Traccar deviceId=%s', device_id)

        return {'status': 'success'}

    @http.route(
        '/traccar/webhook/event',
        type='json',
        auth='public',
        csrf=False,
        methods=['POST'],
    )
    def traccar_event(self, **payload):
        """Receive a Traccar event (overspeed, geofence, alarm, etc.)."""
        device_id = payload.get('deviceId')
        event_type = payload.get('type', 'other')
        raw_event_time = payload.get('serverTime') or payload.get('eventTime')

        if not device_id:
            return {'status': 'error', 'message': 'No deviceId provided'}

        device = request.env['fleet.traccar.device'].sudo().search(
            [('traccar_id', '=', device_id)], limit=1
        )
        vehicle_id = device.vehicle_id.id if device else False

        known_types = [
            'deviceOnline', 'deviceOffline', 'deviceUnknown', 'deviceMoving',
            'deviceStopped', 'deviceOverspeed', 'geofenceEnter', 'geofenceExit',
            'alarm', 'ignitionOn', 'ignitionOff',
        ]
        if event_type not in known_types:
            event_type = 'other'

        parsed_time = request.env['fleet.vehicle']._parse_traccar_datetime(raw_event_time) if raw_event_time else False
        event_time = parsed_time or fields.Datetime.now()

        request.env['fleet.traccar.event'].sudo().create({
            'vehicle_id': vehicle_id,
            'device_id': device.id if device else False,
            'event_type': event_type,
            'event_time': event_time,
            'traccar_event_id': payload.get('id', 0),
            'geofence_id': payload.get('geofenceId', 0),
            'attributes': payload.get('attributes'),
        })
        return {'status': 'success'}
