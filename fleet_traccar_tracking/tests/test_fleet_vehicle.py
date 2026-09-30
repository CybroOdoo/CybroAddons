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
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

class TestFleetVehicle(TransactionCase):

    def setUp(self):
        super(TestFleetVehicle, self).setUp()
        self.Config = self.env['fleet.traccar.config']
        self.Vehicle = self.env['fleet.vehicle']
        self.Device = self.env['fleet.traccar.device']
        
        # Setup config
        self.config = self.Config.create({
            'traccar_url': 'http://test.traccar.com',
            'traccar_username': 'user',
            'traccar_password': 'pass',
        })

        # Setup vehicle
        self.vehicle = self.Vehicle.create({
            'name': 'Test Vehicle',
            'activate_traccar': True,
            'traccar_unique_id': 'unique-123',
        })

    def test_compute_counts(self):
        """Test the computation of related record counts."""
        self.env['fleet.traccar.trip'].create({'vehicle_id': self.vehicle.id})
        self.env['fleet.traccar.event'].create({'vehicle_id': self.vehicle.id, 'event_time': datetime.now()})
        self.env['fleet.traccar.position'].create({'vehicle_id': self.vehicle.id, 'fix_time': datetime.now()})
        
        self.vehicle._compute_trip_count()
        self.vehicle._compute_event_count()
        self.vehicle._compute_position_count()
        
        self.assertEqual(self.vehicle.trip_count, 1)
        self.assertEqual(self.vehicle.event_count, 1)
        self.assertEqual(self.vehicle.position_count, 1)

    @patch('requests.get')
    def test_resolve_traccar_device_id(self, mock_get):
        """Test auto-linking of Traccar devices."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{'id': 99, 'name': 'Dev 99', 'uniqueId': 'unique-123'}]
        mock_get.return_value = mock_response

        dev_id = self.vehicle._resolve_traccar_device_id(self.config)
        self.assertEqual(dev_id, 99)
        self.assertTrue(self.vehicle.traccar_device_id)
        self.assertEqual(self.vehicle.traccar_device_id.traccar_id, 99)

    @patch('requests.get')
    def test_action_refresh_location(self, mock_get):
        """Test fetching the latest location for a vehicle."""
        # Setup device
        device = self.Device.create({'name': 'Dev', 'traccar_id': 99, 'unique_id': 'unique-123'})
        self.vehicle.traccar_device_id = device

        mock_response = MagicMock()
        mock_response.json.return_value = [{
            'id': 1000,
            'latitude': 45.0,
            'longitude': 5.0,
            'speed': 10.0,
            'deviceTime': '2026-03-11T08:47:41Z',
            'attributes': {'batteryLevel': 80}
        }]
        mock_get.return_value = mock_response

        self.vehicle.action_refresh_location()
        self.assertEqual(self.vehicle.last_latitude, 45.0)
        self.assertEqual(self.vehicle.last_speed, 18.5) # 10 knots * 1.852

    @patch('requests.get')
    def test_action_fetch_trips(self, mock_get):
        """Test importing trip reports from Traccar."""
        device = self.Device.create({'name': 'Dev', 'traccar_id': 99, 'unique_id': 'unique-123'})
        self.vehicle.traccar_device_id = device

        mock_response = MagicMock()
        mock_response.json.return_value = [{
            'startTime': '2026-06-01T08:00:00Z',
            'endTime': '2026-06-01T09:00:00Z',
            'distance': 10000,
            'averageSpeed': 10,
            'maxSpeed': 20,
            'startLat': 45.0,
            'startLon': 5.0,
            'endLat': 45.1,
            'endLon': 5.1,
        }]
        mock_get.return_value = mock_response

        self.vehicle.action_fetch_trips()
        trip = self.env['fleet.traccar.trip'].search([('vehicle_id', '=', self.vehicle.id)])
        self.assertTrue(trip)
        self.assertEqual(trip.distance, 10.0)

    def test_process_position(self):
        """Test internal position processing logic."""
        pos_data = {
            'id': 500,
            'latitude': 10.0,
            'longitude': 20.0,
            'speed': 5.0,
            'deviceTime': '2026-06-06T12:00:00Z',
            'attributes': {'batteryLevel': 90, 'motion': True}
        }
        self.vehicle._process_position(pos_data)
        self.assertEqual(self.vehicle.last_latitude, 10.0)
        self.assertEqual(self.vehicle.current_status, 'running') # speed > 2
        
        # Test offline status due to stale data
        old_time = (datetime.utcnow() - timedelta(minutes=20)).strftime('%Y-%m-%dT%H:%M:%SZ')
        pos_data_stale = {
            'id': 501,
            'latitude': 10.0,
            'longitude': 20.0,
            'speed': 0,
            'deviceTime': old_time,
        }
        self.vehicle._process_position(pos_data_stale)
        self.assertEqual(self.vehicle.current_status, 'offline')
