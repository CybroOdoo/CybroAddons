# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase
from unittest.mock import patch


class MockResponse:
    """Helper class to simulate requests.get().json() behavior"""

    def __init__(self, json_data):
        self.json_data = json_data

    def json(self):
        return self.json_data


class TestLoginLog(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestLoginLog, cls).setUpClass()
        # Find or create a test user to test authentication logging
        cls.test_user = cls.env['res.users'].create({
            'name': 'Log Test User',
            'login': 'test_log_user',
            'email': 'test_log@example.com',
        })
        cls.param_have_key = 'export_delete_login_log.have_api_key'
        cls.param_api_key = 'export_delete_login_log.ipapi_key'

    @patch('requests.get')
    @patch('odoo.addons.auth_passkey.models.res_users.ResUsers._check_credentials')
    def test_01_successful_login_log_creation(self, mock_super, mock_get):
        """Test successful authentication logging when ipapi returns valid data without API key."""
        # 1. Mock the super call so it doesn't crash on Odoo 19 passkey validations
        mock_super.return_value = True

        # 2. Setup system parameters
        self.env['ir.config_parameter'].sudo().set_param(self.param_have_key, False)

        # 3. Mock external requests in sequence: 1st call for ipify, 2nd call for ipapi
        mock_get.side_effect = [
            MockResponse({'ip': '8.8.8.8'}),
            MockResponse({
                'latitude': 37.386,
                'longitude': -122.0838,
                'city': 'Mountain View',
                'region': 'California',
                'country_name': 'United States',
                'postal': '94035',
                'timezone': 'America/Los_Angeles',
                'error': False,
                'reason': None
            })
        ]

        # 4. Call _check_credentials on the user
        self.test_user._check_credentials('dummy_password', {})

        # 5. Assert that a log record was generated correctly
        log = self.env['login.log'].search([('name', '=', self.test_user.name)], order='id desc', limit=1)

        self.assertTrue(log, "Login log record was not created.")
        self.assertEqual(log.ip_address, '8.8.8.8')
        self.assertEqual(log.geo_loc, "37.386, -122.0838")
        self.assertEqual(log.address, "Mountain View, California, United States")
        self.assertEqual(log.postal_code, '94035')
        self.assertEqual(log.time_zone, 'America/Los_Angeles')
        self.assertFalse(log.remark, "Remark should be empty on successful tracking.")

    @patch('requests.get')
    @patch('odoo.addons.auth_passkey.models.res_users.ResUsers._check_credentials')
    def test_02_login_log_rate_limited(self, mock_super, mock_get):
        """Test log creation when the IP API returns a 'RateLimited' error."""
        mock_super.return_value = True
        self.env['ir.config_parameter'].sudo().set_param(self.param_have_key, False)

        # Mock ipify success but ipapi rate limit failure
        mock_get.side_effect = [
            MockResponse({'ip': '8.8.8.8'}),
            MockResponse({
                'error': True,
                'reason': 'RateLimited'
            })
        ]

        self.test_user._check_credentials('dummy_password', {})

        log = self.env['login.log'].search([('name', '=', self.test_user.name)], order='id desc', limit=1)

        self.assertTrue(log)
        self.assertEqual(log.ip_address, '8.8.8.8')
        self.assertEqual(log.remark, "Free quota exceeded", "The custom remark translation mapping failed.")

    @patch('requests.get')
    @patch('odoo.addons.auth_passkey.models.res_users.ResUsers._check_credentials')
    def test_03_login_log_with_api_key(self, mock_super, mock_get):
        """Test that the request URL structure adapts when an API key configuration is active."""
        mock_super.return_value = True
        self.env['ir.config_parameter'].sudo().set_param(self.param_have_key, True)
        self.env['ir.config_parameter'].sudo().set_param(self.param_api_key, 'secret_token_123')

        mock_get.side_effect = [
            MockResponse({'ip': '1.1.1.1'}),
            MockResponse({'city': 'Sydney', 'region': 'NSW', 'country_name': 'Australia', 'error': False})
        ]

        self.test_user._check_credentials('dummy_password', {})

        # Assert that the second HTTP get request was executed using the key URL string
        expected_url_call = "https://ipapi.co/1.1.1.1/json/?key=secret_token_123"
        mock_get.assert_any_call(expected_url_call)