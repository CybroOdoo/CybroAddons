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
#############################################################################

from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import ValidationError
from odoo.tests import HttpCase, TransactionCase, new_test_user, tagged

MODEL_GET = 'odoo.addons.user_weather_map.models.res_users.requests.get'
CTRL = 'odoo.addons.user_weather_map.controllers.user_weather_map'


def _response(payload, status=200):
    resp = MagicMock(status_code=status)
    resp.json.return_value = payload
    return resp


@tagged('post_install', '-at_install')
class TestWeatherSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(cls.env, login='weather_user', groups='base.group_user')

    def test_key_and_city_are_stripped(self):
        with patch(MODEL_GET, return_value=_response({'cod': 200})) as get:
            self.user.write({'api_key': '  abc123 \n', 'location_set': 'manual', 'city': ' Kochi '})
        self.assertEqual((self.user.api_key, self.user.city), ('abc123', 'Kochi'))
        self.assertEqual(get.call_args.kwargs['params'], {'q': 'Kochi', 'appid': 'abc123'})

    def test_create_strips_key(self):
        with patch(MODEL_GET, return_value=_response({'cod': 200})):
            user = new_test_user(self.env, login='weather_new', groups='base.group_user',
                                 api_key=' key1 ')
        self.assertEqual(user.api_key, 'key1')

    def test_auto_location_validates_key_with_default_city(self):
        with patch(MODEL_GET, return_value=_response({'cod': 200})) as get:
            self.user.write({'api_key': 'abc123', 'location_set': 'auto'})
        self.assertEqual(get.call_args.kwargs['params'], {'q': 'London', 'appid': 'abc123'})

    def test_invalid_key_shows_api_message(self):
        msg = 'Invalid API key. Please see https://openweathermap.org/faq#error401 for more info.'
        with patch(MODEL_GET, return_value=_response({'cod': 401, 'message': msg})), \
                self.assertRaisesRegex(ValidationError, 'Invalid API key'):
            self.user.write({'api_key': 'bad'})

    def test_manual_location_needs_city(self):
        with patch(MODEL_GET) as get, self.assertRaises(ValidationError):
            self.user.write({'api_key': 'abc123', 'location_set': 'manual', 'city': False})
        get.assert_not_called()

    def test_connection_error(self):
        with patch(MODEL_GET, side_effect=requests.exceptions.ConnectionError('offline')), \
                self.assertRaisesRegex(ValidationError, 'Could not connect'):
            self.user.write({'api_key': 'abc123'})

    def test_no_key_no_check(self):
        with patch(MODEL_GET) as get:
            self.user.write({'city': 'Kochi'})
        get.assert_not_called()

    def test_key_hidden_from_other_users(self):
        other = new_test_user(self.env, login='weather_other', groups='base.group_user')
        self.assertNotIn('api_key', self.env['res.users'].with_user(other).fields_get())


@tagged('post_install', '-at_install')
class TestWeatherController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(cls.env, login='weather_http', password='weather_http',
                                 groups='base.group_user')

    def _set(self, **vals):
        with patch(MODEL_GET, return_value=_response({'cod': 200})):
            self.user.write(vals)

    def _call(self):
        self.authenticate('weather_http', 'weather_http')
        return self.make_jsonrpc_request('/weather/notification/check', {})

    def test_no_key(self):
        self.assertEqual(self._call(), {'data': False})

    def test_manual_city(self):
        self._set(api_key='abc123', location_set='manual', city='Kochi')
        with patch(f'{CTRL}.requests.get', return_value=_response({'name': 'Kochi', 'main': {'temp': 300}})) as get:
            self.assertEqual(self._call()['name'], 'Kochi')
        self.assertEqual(get.call_args.kwargs['params'], {'q': 'Kochi', 'appid': 'abc123'})

    def test_auto_from_ip_location(self):
        self._set(api_key='abc123', location_set='auto')
        geo = MagicMock(status_code=200, latlng=[9.9312, 76.2673])
        with patch(f'{CTRL}.geocoder.ip', return_value=geo), \
                patch(f'{CTRL}.requests.get', return_value=_response({'name': 'Kochi'})) as get:
            self.assertEqual(self._call()['name'], 'Kochi')
        self.assertEqual(get.call_args.kwargs['params'], {'lat': 9.93, 'lon': 76.27, 'appid': 'abc123'})

    def test_auto_falls_back_to_partner_city(self):
        self._set(api_key='abc123', location_set='auto')
        self.user.partner_id.city = 'Kochi'
        with patch(f'{CTRL}.geocoder.ip', return_value=MagicMock(status_code=500, latlng=None)), \
                patch(f'{CTRL}.requests.get', return_value=_response({'name': 'Kochi'})):
            self.assertEqual(self._call()['name'], 'Kochi')

    def test_auto_failure_is_logged(self):
        self._set(api_key='abc123', location_set='auto')
        with patch(f'{CTRL}.geocoder.ip', side_effect=OSError('offline')), \
                self.assertLogs(CTRL, level='WARNING'):
            self.assertEqual(self._call(), {'data': False})

    def test_manual_failure_is_logged(self):
        self._set(api_key='abc123', location_set='manual', city='Kochi')
        with patch(f'{CTRL}.requests.get', side_effect=requests.exceptions.Timeout()), \
                self.assertLogs(CTRL, level='WARNING'):
            self.assertEqual(self._call(), {'data': False})
