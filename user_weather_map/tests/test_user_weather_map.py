# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import patch
import requests
from odoo.tests import TransactionCase, tagged
from odoo.addons.user_weather_map.controllers.user_weather_map import WeatherNotification


class MockRequest:
    def __init__(self, env):
        self.env = env


class MockGeocoderResponse:
    def __init__(self, status_code, latlng):
        self.status_code = status_code
        self.latlng = latlng


@tagged('post_install', '-at_install')
class TestUserWeatherMap(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = WeatherNotification()
        cls.mock_request = MockRequest(cls.env)

    def setUp(self):
        super().setUp()
        # Ensure test user credentials are reset
        self.env.user.write({
            'api_key': False,
            'location_set': 'auto',
            'city': False,
        })

    def test_01_weather_notification_no_api_key(self):
        """Test that weather notification returns {'data': False} when API Key is not set."""
        with patch('odoo.addons.user_weather_map.controllers.user_weather_map.request', self.mock_request):
            res = self.controller.weather_notification()
            self.assertEqual(res, {'data': False})

    def test_02_weather_notification_auto_success(self):
        """Test weather notification with location 'auto' and successful geocoding / OWM response."""
        self.env.user.write({
            'api_key': 'test_api_key',
            'location_set': 'auto',
        })

        mock_geo_resp = MockGeocoderResponse(status_code=200, latlng=[51.5074, -0.1278])
        mock_weather_json = {
            'weather': [{'main': 'Clear', 'description': 'clear sky'}],
            'main': {'temp': 288.15}
        }

        with patch('odoo.addons.user_weather_map.controllers.user_weather_map.request', self.mock_request), \
             patch('geocoder.ip', return_value=mock_geo_resp) as mock_geocoder, \
             patch('requests.get') as mock_requests_get:
            
            mock_requests_get.return_value.status_code = 200
            mock_requests_get.return_value.json.return_value = mock_weather_json

            res = self.controller.weather_notification()

            mock_geocoder.assert_called_once_with('me')
            mock_requests_get.assert_called_once_with(
                'https://api.openweathermap.org/data/2.5/weather?lat=51.51&lon=-0.13&appid=test_api_key',
                timeout=20
            )
            self.assertEqual(res, mock_weather_json)

    def test_03_weather_notification_auto_geocoder_failure(self):
        """Test weather notification with location 'auto' when geocoder returns error status."""
        self.env.user.write({
            'api_key': 'test_api_key',
            'location_set': 'auto',
        })

        mock_geo_resp = MockGeocoderResponse(status_code=403, latlng=None)

        with patch('odoo.addons.user_weather_map.controllers.user_weather_map.request', self.mock_request), \
             patch('geocoder.ip', return_value=mock_geo_resp), \
             patch('requests.get') as mock_requests_get:

            res = self.controller.weather_notification()
            
            mock_requests_get.assert_not_called()
            self.assertEqual(res, {'data': False})

    def test_04_weather_notification_auto_exception(self):
        """Test weather notification with location 'auto' handles exceptions gracefully."""
        self.env.user.write({
            'api_key': 'test_api_key',
            'location_set': 'auto',
        })

        with patch('odoo.addons.user_weather_map.controllers.user_weather_map.request', self.mock_request), \
             patch('geocoder.ip', side_effect=Exception("Geocoding failed")):
            
            res = self.controller.weather_notification()
            self.assertEqual(res, {'data': False})

    def test_05_weather_notification_manual_success(self):
        """Test weather notification with location 'manual' and successful OWM response."""
        # Use patch to bypass ResUsers check_city constraint when writing city
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {'cod': 200}
            self.env.user.write({
                'api_key': 'test_api_key',
                'location_set': 'manual',
                'city': 'Tokyo',
            })

        mock_weather_json = {
            'weather': [{'main': 'Rain', 'description': 'light rain'}],
            'main': {'temp': 293.15}
        }

        with patch('odoo.addons.user_weather_map.controllers.user_weather_map.request', self.mock_request), \
             patch('requests.get') as mock_requests_get:
            
            mock_requests_get.return_value.status_code = 200
            mock_requests_get.return_value.json.return_value = mock_weather_json

            res = self.controller.weather_notification()

            mock_requests_get.assert_called_once_with(
                'https://api.openweathermap.org/data/2.5/weather?q=Tokyo&appid=test_api_key',
                timeout=20
            )
            self.assertEqual(res, mock_weather_json)

    def test_06_weather_notification_manual_exception(self):
        """Test weather notification with location 'manual' handles exceptions gracefully."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {'cod': 200}
            self.env.user.write({
                'api_key': 'test_api_key',
                'location_set': 'manual',
                'city': 'Tokyo',
            })

        with patch('odoo.addons.user_weather_map.controllers.user_weather_map.request', self.mock_request), \
             patch('requests.get', side_effect=requests.exceptions.Timeout("Connection timed out")):
            
            res = self.controller.weather_notification()
            self.assertEqual(res, {'data': False})
