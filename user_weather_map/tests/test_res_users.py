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
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a test user
        cls.test_user = cls.env['res.users'].create({
            'name': 'Weather Test User',
            'login': 'weather_test_user@example.com',
            'email': 'weather_test_user@example.com',
            'api_key': False,
            'city': False,
        })

    def test_01_check_city_no_api_key(self):
        """Test that city validation is skipped when API Key is not set."""
        # Writing a city with no api_key should not trigger requests.get
        with patch('requests.get') as mock_get:
            self.test_user.write({
                'city': 'Paris'
            })
            mock_get.assert_not_called()
            self.assertEqual(self.test_user.city, 'Paris')

    def test_02_check_city_valid(self):
        """Test that city validation passes when OpenWeatherMap returns code 200."""
        mock_response = {'cod': 200, 'name': 'London'}
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            self.test_user.write({
                'api_key': 'valid_api_key_123',
                'city': 'London'
            })

            mock_get.assert_called_once_with(
                'https://api.openweathermap.org/data/2.5/weather?q=London&appid=valid_api_key_123',
                timeout=20
            )

    def test_03_check_city_invalid(self):
        """Test that city validation raises ValidationError when OpenWeatherMap returns an error code."""
        mock_response = {'cod': 404, 'message': 'city not found'}
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            with self.assertRaises(ValidationError) as context:
                self.test_user.write({
                    'api_key': 'valid_api_key_123',
                    'city': 'InvalidCityName'
                })

            self.assertIn('city not found', str(context.exception))
