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
import json

from odoo.tests.common import HttpCase

class TestFleetTraccarController(HttpCase):

    def setUp(self):
        super(TestFleetTraccarController, self).setUp()
        self.device = self.env['fleet.traccar.device'].create({
            'name': 'Test Device',
            'traccar_id': 123,
            'unique_id': 'unique-123',
        })
        self.vehicle = self.env['fleet.vehicle'].create({
            'name': 'Test Vehicle',
            'traccar_device_id': self.device.id
        })

    def test_traccar_position_webhook(self):
        """Test the /traccar/webhook/position endpoint."""
        payload = {
            'params': {
                'deviceId': 123,
                'latitude': 45.0,
                'longitude': 5.0,
                'speed': 10.0,
                'fixTime': '2026-06-06T12:00:00Z'
            }
        }
        
        response = self.url_open(
            '/traccar/webhook/position',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.vehicle.last_latitude, 45.0)

    def test_traccar_event_webhook(self):
        """Test the /traccar/webhook/event endpoint."""
        payload = {
            'params': {
                'deviceId': 123,
                'type': 'deviceOverspeed',
                'serverTime': '2026-06-06T12:30:00Z',
                'id': 999,
                'attributes': {'speed': 120}
            }
        }
        
        response = self.url_open(
            '/traccar/webhook/event',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        
        event = self.env['fleet.traccar.event'].search([('traccar_event_id', '=', 999)])
        self.assertTrue(event)
        self.assertEqual(event.event_type, 'deviceOverspeed')
        self.assertEqual(event.vehicle_id, self.vehicle)
