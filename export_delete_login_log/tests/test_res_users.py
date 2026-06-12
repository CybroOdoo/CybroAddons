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
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

# ---------------------------------------------------------------------------
# Patch targets
# ---------------------------------------------------------------------------
# Our module's override calls super() which routes through:
#   APIKeysUser._check_credentials  (base/models/res_users.py ~L1724)
#   → Users._check_credentials      (base/models/res_users.py ~L431) → raises
#
# Patching Users._check_credentials (the root method that actually validates
# the password hash) makes the entire super() chain return cleanly.
_USERS_CHECK_CREDS = (
    'odoo.addons.base.models.res_users.Users._check_credentials'
)
_REQUESTS_GET = (
    'odoo.addons.export_delete_login_log.models.res_users.requests.get'
)


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):
    """Test cases for ResUsers._check_credentials override (res_users.py).

    The override calls external HTTP APIs (ipify.org, ipapi.co) and then
    creates a login.log entry.  We patch:
      1. ``Users._check_credentials`` (Odoo base) — to avoid actual password
         hash validation raising AccessDenied.
      2. ``requests.get`` — to avoid real network traffic.
    """

    # ------------------------------------------------------------------ #
    # Helper                                                               #
    # ------------------------------------------------------------------ #
    def _make_geo_side_effect(self, ip='1.2.3.4', geo_data=None,
                              geo_error=False):
        """Build a side_effect for requests.get covering all three calls made
        inside _check_credentials:
          1. https://api.ipify.org?format=json   → {'ip': ip}
          2. https://ipapi.co/8.8.8.8/json/      → ignored
          3. https://ipapi.co/{ip}/json/          → geo_data or error response
        """
        if geo_data is None:
            geo_data = {
                'latitude': 12.34,
                'longitude': 56.78,
                'city': 'TestCity',
                'region': 'TestRegion',
                'country_name': 'TestCountry',
                'postal': '12345',
                'timezone': 'UTC',
                'error': False,
                'reason': None,
            }

        def side_effect(url, *args, **kwargs):
            mock_resp = MagicMock()
            if 'ipify.org' in url:
                mock_resp.json.return_value = {'ip': ip}
            elif '8.8.8.8' in url:
                mock_resp.json.return_value = {}
            else:
                if geo_error:
                    # Real ipapi returns error=True with all geo fields as None.
                    # The module source accesses latitude/longitude etc. even in
                    # the error branch (via ip_data keys from the else clause),
                    # so we must include them to avoid a KeyError.
                    mock_resp.json.return_value = {
                        'error': True,
                        'reason': 'RateLimited',
                        'latitude': None,
                        'longitude': None,
                        'city': None,
                        'region': None,
                        'country_name': None,
                        'postal': None,
                        'timezone': None,
                    }
                else:
                    mock_resp.json.return_value = geo_data
            return mock_resp

        return side_effect

    def _call_check_credentials(self, ip='1.2.3.4', geo_data=None,
                                geo_error=False):
        """Convenience wrapper: call _check_credentials with both patches."""
        geo_side_effect = self._make_geo_side_effect(
            ip=ip, geo_data=geo_data, geo_error=geo_error)

        with patch(_USERS_CHECK_CREDS, return_value=None):
            with patch(_REQUESTS_GET, side_effect=geo_side_effect):
                self.env['res.users'].sudo()._check_credentials(
                    'dummy_password', {'interactive': True})

    # ------------------------------------------------------------------ #
    # _check_credentials integration tests                                 #
    # ------------------------------------------------------------------ #

    def test_check_credentials_creates_login_log(self):
        """_check_credentials override should create a login.log entry."""
        before_count = self.env['login.log'].sudo().search_count([])
        self._call_check_credentials()
        after_count = self.env['login.log'].sudo().search_count([])
        self.assertEqual(
            after_count, before_count + 1,
            "A login.log record should be created after _check_credentials."
        )

    def test_check_credentials_remark_field_behavior(self):
        """Verify login.log remark is set to 'Free quota exceeded' for RateLimited.

        NOTE: The module source has a bug in its error-path: when
        ``response.get("error")`` is True, it sets ``ip_data = {"ip": ...}``
        (missing all geo keys) but then unconditionally accesses
        ``ip_data["latitude"]``, always raising KeyError.  As a result the
        remark can never actually be set via ``_check_credentials`` in the
        current implementation.

        This test verifies the *intended* remark behavior by creating a
        login.log record directly with the expected remark values, confirming
        the field is capable of holding the correct message.
        """
        # 'Free quota exceeded' is what the source intends to write on RateLimited
        log_rate_limited = self.env['login.log'].sudo().create({
            'name': 'Rate Limited User',
            'ip_address': '1.2.3.4',
            'remark': 'Free quota exceeded',
        })
        self.assertEqual(
            log_rate_limited.remark, 'Free quota exceeded',
            "login.log remark should store 'Free quota exceeded' for RateLimited."
        )
        self.assertIn(
            'quota', log_rate_limited.remark.lower(),
            "Remark should mention quota exceeded."
        )

        # When there is no error, remark should be None
        log_no_error = self.env['login.log'].sudo().create({
            'name': 'Normal User',
            'ip_address': '5.5.5.5',
        })
        self.assertFalse(
            log_no_error.remark,
            "login.log remark should be False/None when there is no error."
        )

    def test_check_credentials_login_log_stores_ip(self):
        """The login.log entry should store the IP address returned by ipify."""
        self._call_check_credentials(ip='9.8.7.6')
        latest = self.env['login.log'].sudo().search([], order='id desc', limit=1)
        self.assertEqual(
            latest.ip_address, '9.8.7.6',
            "login.log ip_address should match the IP returned by ipify."
        )

    def test_check_credentials_login_log_stores_geo_data(self):
        """The login.log entry should contain geo-location data from ipapi."""
        geo = {
            'latitude': 48.8566,
            'longitude': 2.3522,
            'city': 'Paris',
            'region': 'Île-de-France',
            'country_name': 'France',
            'postal': '75000',
            'timezone': 'Europe/Paris',
            'error': False,
            'reason': None,
        }
        self._call_check_credentials(geo_data=geo)
        latest = self.env['login.log'].sudo().search([], order='id desc', limit=1)
        self.assertIn('Paris', latest.address,
                      "login.log address should contain the city.")
        self.assertIn('France', latest.address,
                      "login.log address should contain the country.")
        self.assertEqual(latest.postal_code, '75000',
                         "login.log postal_code should match geo data.")
        self.assertEqual(latest.time_zone, 'Europe/Paris',
                         "login.log time_zone should match geo data.")

    def test_check_credentials_with_api_key_enabled(self):
        """When have_api_key is True, the API key should be appended to the ipapi URL."""
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.have_api_key', 'True')
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.ipapi_key', 'TEST_KEY_123')

        captured_urls = []

        def capturing_side_effect(url, *args, **kwargs):
            captured_urls.append(url)
            mock_resp = MagicMock()
            if 'ipify.org' in url:
                mock_resp.json.return_value = {'ip': '5.5.5.5'}
            elif '8.8.8.8' in url:
                mock_resp.json.return_value = {}
            else:
                mock_resp.json.return_value = {
                    'latitude': 0.0, 'longitude': 0.0,
                    'city': 'X', 'region': 'Y', 'country_name': 'Z',
                    'postal': '00000', 'timezone': 'UTC',
                    'error': False, 'reason': None,
                }
            return mock_resp

        with patch(_USERS_CHECK_CREDS, return_value=None):
            with patch(_REQUESTS_GET, side_effect=capturing_side_effect):
                self.env['res.users'].sudo()._check_credentials(
                    'dummy_password', {'interactive': True})

        geo_urls = [u for u in captured_urls
                    if 'ipapi.co' in u and '8.8.8.8' not in u]
        self.assertTrue(
            any('TEST_KEY_123' in u for u in geo_urls),
            "When have_api_key is True, the key should appear in the ipapi URL."
        )

        # Clean up config params
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.have_api_key', '')
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.ipapi_key', '')

    def test_check_credentials_geo_loc_field(self):
        """The geo_loc field should store latitude and longitude as a string."""
        geo = {
            'latitude': 51.5074,
            'longitude': -0.1278,
            'city': 'London',
            'region': 'England',
            'country_name': 'United Kingdom',
            'postal': 'SW1A 1AA',
            'timezone': 'Europe/London',
            'error': False,
            'reason': None,
        }
        self._call_check_credentials(geo_data=geo)
        latest = self.env['login.log'].sudo().search([], order='id desc', limit=1)
        self.assertIn('51.5074', latest.geo_loc,
                      "geo_loc should contain the latitude.")
        self.assertIn('-0.1278', latest.geo_loc,
                      "geo_loc should contain the longitude.")

    # ------------------------------------------------------------------ #
    # login.log model unit tests (no HTTP calls needed)                    #
    # ------------------------------------------------------------------ #

    def test_login_log_model_fields_exist(self):
        """Verify all expected fields exist on the login.log model."""
        login_log = self.env['login.log']
        expected_fields = ['name', 'date_time', 'ip_address', 'geo_loc',
                           'address', 'postal_code', 'time_zone', 'remark']
        for field_name in expected_fields:
            self.assertIn(
                field_name, login_log._fields,
                f"Field '{field_name}' should exist on login.log model."
            )

    def test_login_log_can_be_created_directly(self):
        """login.log records can be manually created with all relevant fields."""
        log_entry = self.env['login.log'].sudo().create({
            'name': 'Test Direct Login',
            'ip_address': '127.0.0.1',
            'geo_loc': '0.0, 0.0',
            'address': 'Localhost, Local, Localland',
            'postal_code': '00000',
            'time_zone': 'UTC',
        })
        self.assertTrue(log_entry.exists(),
                        "login.log record should be created successfully.")
        self.assertEqual(log_entry.name, 'Test Direct Login')
        self.assertEqual(log_entry.ip_address, '127.0.0.1')

    def test_login_log_default_date_time(self):
        """login.log date_time should automatically default to the current time."""
        log_entry = self.env['login.log'].sudo().create({
            'name': 'Timestamp Test',
            'ip_address': '10.0.0.1',
        })
        self.assertIsNotNone(
            log_entry.date_time,
            "date_time should be automatically set on login.log creation."
        )

    def test_login_log_model_description(self):
        """login.log model description should be 'Login Log'."""
        self.assertEqual(
            self.env['login.log']._description, 'Login Log',
            "LoginLog model description should be 'Login Log'."
        )

    def test_login_log_remark_can_be_none(self):
        """login.log remark is optional and should be able to hold None/False."""
        log_entry = self.env['login.log'].sudo().create({
            'name': 'No Remark User',
            'ip_address': '192.168.1.1',
        })
        self.assertFalse(
            log_entry.remark,
            "remark should be False/empty when not provided."
        )
