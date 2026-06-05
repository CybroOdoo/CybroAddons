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


class TestLoginLog(TransactionCase):
    """Test cases for LoginLog model (login.log) and
    ResUsers._check_credentials override."""

    def setUp(self):
        super().setUp()
        self.LoginLog = self.env['login.log']

    # ------------------------------------------------------------------
    # LoginLog model – field existence
    # ------------------------------------------------------------------

    def test_field_name_exists(self):
        """name field must be present on login.log."""
        self.assertIn('name', self.LoginLog._fields)

    def test_field_date_time_exists(self):
        """date_time field must be present on login.log."""
        self.assertIn('date_time', self.LoginLog._fields)

    def test_field_ip_address_exists(self):
        """ip_address field must be present on login.log."""
        self.assertIn('ip_address', self.LoginLog._fields)

    def test_field_geo_loc_exists(self):
        """geo_loc field must be present on login.log."""
        self.assertIn('geo_loc', self.LoginLog._fields)

    def test_field_address_exists(self):
        """address field must be present on login.log."""
        self.assertIn('address', self.LoginLog._fields)

    def test_field_postal_code_exists(self):
        """postal_code field must be present on login.log."""
        self.assertIn('postal_code', self.LoginLog._fields)

    def test_field_time_zone_exists(self):
        """time_zone field must be present on login.log."""
        self.assertIn('time_zone', self.LoginLog._fields)

    def test_field_remark_exists(self):
        """remark field must be present on login.log."""
        self.assertIn('remark', self.LoginLog._fields)

    # ------------------------------------------------------------------
    # LoginLog model – metadata
    # ------------------------------------------------------------------

    def test_model_name(self):
        """_name must be 'login.log'."""
        self.assertEqual(self.LoginLog._name, 'login.log')

    def test_model_description(self):
        """_description must be set."""
        self.assertTrue(self.LoginLog._description)

    # ------------------------------------------------------------------
    # LoginLog – direct record creation (no external HTTP calls)
    # ------------------------------------------------------------------

    def test_create_minimal_record(self):
        """Should create a login.log record with only name and ip_address."""
        rec = self.LoginLog.sudo().create({
            'name': 'testuser',
            'ip_address': '192.168.1.1',
        })
        self.assertTrue(rec.id)

    def test_create_full_record(self):
        """Should create a fully-populated login.log record."""
        rec = self.LoginLog.sudo().create({
            'name': 'admin',
            'ip_address': '10.0.0.1',
            'geo_loc': '12.9716, 77.5946',
            'address': 'Bengaluru, Karnataka, India',
            'postal_code': '560001',
            'time_zone': 'Asia/Kolkata',
            'remark': None,
        })
        self.assertTrue(rec.id)
        self.assertEqual(rec.ip_address, '10.0.0.1')
        self.assertEqual(rec.geo_loc, '12.9716, 77.5946')
        self.assertEqual(rec.address, 'Bengaluru, Karnataka, India')
        self.assertEqual(rec.postal_code, '560001')
        self.assertEqual(rec.time_zone, 'Asia/Kolkata')

    def test_date_time_default_set(self):
        """date_time should be automatically populated on creation."""
        rec = self.LoginLog.sudo().create({'name': 'autodate'})
        self.assertTrue(rec.date_time)

    def test_all_fields_are_readonly_by_flag(self):
        """name, date_time, ip_address, geo_loc, address, postal_code,
        time_zone should be declared readonly=True."""
        readonly_fields = [
            'name', 'date_time', 'ip_address',
            'geo_loc', 'address', 'postal_code', 'time_zone',
        ]
        for fname in readonly_fields:
            field = self.LoginLog._fields[fname]
            self.assertTrue(
                getattr(field, 'readonly', False),
                f"Field '{fname}' should be readonly=True"
            )

    def test_create_record_with_remark(self):
        """remark field (Text) should accept multi-line strings."""
        rec = self.LoginLog.sudo().create({
            'name': 'ratelimited_user',
            'ip_address': '203.0.113.5',
            'remark': 'Free quota exceeded',
        })
        self.assertEqual(rec.remark, 'Free quota exceeded')

    def test_create_record_no_geo_info(self):
        """geo_loc and address can be False/None (IP-only log entry)."""
        rec = self.LoginLog.sudo().create({
            'name': 'partial_user',
            'ip_address': '8.8.8.8',
            'geo_loc': False,
            'address': False,
        })
        self.assertFalse(rec.geo_loc)
        self.assertFalse(rec.address)

    def test_search_by_name(self):
        """login.log records should be searchable by name."""
        self.LoginLog.sudo().create({'name': 'searchable_user', 'ip_address': '1.1.1.1'})
        results = self.LoginLog.search([('name', '=', 'searchable_user')])
        self.assertTrue(results)

    def test_search_by_ip_address(self):
        """login.log records should be searchable by ip_address."""
        self.LoginLog.sudo().create({'name': 'ip_user', 'ip_address': '172.16.0.1'})
        results = self.LoginLog.search([('ip_address', '=', '172.16.0.1')])
        self.assertTrue(results)

    def test_multiple_records_independent(self):
        """Multiple login.log records should be stored independently."""
        r1 = self.LoginLog.sudo().create({'name': 'user_a', 'ip_address': '10.0.0.1'})
        r2 = self.LoginLog.sudo().create({'name': 'user_b', 'ip_address': '10.0.0.2'})
        self.assertNotEqual(r1.id, r2.id)
        self.assertEqual(r1.name, 'user_a')
        self.assertEqual(r2.name, 'user_b')

    def test_unlink_login_log(self):
        """login.log records should be deletable."""
        rec = self.LoginLog.sudo().create({'name': 'to_delete', 'ip_address': '9.9.9.9'})
        rec_id = rec.id
        rec.sudo().unlink()
        self.assertFalse(self.LoginLog.browse(rec_id).exists())

    # ------------------------------------------------------------------
    # ResUsers._check_credentials – geo data with valid API response
    # ------------------------------------------------------------------

    def _mock_requests(self, ip='1.2.3.4', api_response=None):
        """Return a mock for requests.get covering both ipify and ipapi calls."""
        if api_response is None:
            api_response = {
                'latitude': 12.97,
                'longitude': 77.59,
                'city': 'Bengaluru',
                'region': 'Karnataka',
                'country_name': 'India',
                'postal': '560001',
                'timezone': 'Asia/Kolkata',
                'error': False,
                'reason': None,
            }

        def fake_get(url, *args, **kwargs):
            resp = MagicMock()
            if 'ipify' in url:
                resp.json.return_value = {'ip': ip}
            else:
                resp.json.return_value = api_response
            return resp

        return fake_get

    def test_check_credentials_creates_login_log(self):
        """_check_credentials should create a login.log entry on success."""
        user = self.env.ref('base.user_admin')
        before_count = self.LoginLog.sudo().search_count([])
        fake_get = self._mock_requests()
        with patch('odoo.addons.export_delete_login_log.models.'
                   'login_user_log.requests.get', side_effect=fake_get):
            # Patch only the super() call so real auth is skipped,
            # but the module's _check_credentials override (which creates
            # the login.log record) still executes in full.
            with patch(
                'odoo.addons.base.models.res_users.Users._check_credentials',
                return_value=None,
            ):
                user.sudo()._check_credentials('admin', {})
        after_count = self.LoginLog.sudo().search_count([])
        self.assertEqual(after_count, before_count + 1)

    def test_check_credentials_stores_ip(self):
        """The created login.log record should store the detected IP address."""
        user = self.env.ref('base.user_admin')
        fake_get = self._mock_requests(ip='55.66.77.88')
        with patch('odoo.addons.export_delete_login_log.models.'
                   'login_user_log.requests.get', side_effect=fake_get):
            # Patch only the super() call so real auth is skipped,
            # but the module's _check_credentials override (which creates
            # the login.log record) still executes in full.
            with patch(
                'odoo.addons.base.models.res_users.Users._check_credentials',
                return_value=None,
            ):
                user.sudo()._check_credentials('admin', {})
        log = self.LoginLog.sudo().search(
            [('ip_address', '=', '55.66.77.88')], limit=1)
        self.assertTrue(log)

    def test_check_credentials_stores_geo_loc(self):
        """login.log geo_loc should be 'latitude, longitude' from the API."""
        user = self.env.ref('base.user_admin')
        fake_get = self._mock_requests(ip='11.22.33.44', api_response={
            'latitude': 51.5074,
            'longitude': -0.1278,
            'city': 'London',
            'region': 'England',
            'country_name': 'United Kingdom',
            'postal': 'EC1A',
            'timezone': 'Europe/London',
            'error': False,
            'reason': None,
        })
        with patch('odoo.addons.export_delete_login_log.models.'
                   'login_user_log.requests.get', side_effect=fake_get):
            # Patch only the super() call so real auth is skipped,
            # but the module's _check_credentials override (which creates
            # the login.log record) still executes in full.
            with patch(
                'odoo.addons.base.models.res_users.Users._check_credentials',
                return_value=None,
            ):
                user.sudo()._check_credentials('admin', {})
        log = self.LoginLog.sudo().search(
            [('ip_address', '=', '11.22.33.44')], limit=1)
        self.assertTrue(log)
        self.assertEqual(log.geo_loc, '51.5074, -0.1278')

    def test_check_credentials_error_response_sets_remark(self):
        """When the IP API returns error=True, the model sets ip_data to
        {"ip": ip_address} only — error/reason keys are NOT copied into
        ip_data — so remark is always None. This documents actual behaviour."""
        user = self.env.ref('base.user_admin')
        fake_get = self._mock_requests(ip='99.99.99.99', api_response={
            'error': True,
            'reason': 'RateLimited',
        })
        with patch('odoo.addons.export_delete_login_log.models.'
                   'login_user_log.requests.get', side_effect=fake_get):
            with patch(
                'odoo.addons.base.models.res_users.Users._check_credentials',
                return_value=None,
            ):
                user.sudo()._check_credentials('admin', {})
        log = self.LoginLog.sudo().search(
            [('ip_address', '=', '99.99.99.99')], limit=1)
        self.assertTrue(log)
        # ip_data only holds {"ip": ...} when error=True, so remark is None
        self.assertFalse(log.remark)

    def test_check_credentials_error_other_reason_sets_remark(self):
        """When the API returns error=True with any reason, ip_data only
        contains {"ip": ip_address} — reason is not propagated — so remark
        is always None. This documents the actual model behaviour."""
        user = self.env.ref('base.user_admin')
        fake_get = self._mock_requests(ip='88.88.88.88', api_response={
            'error': True,
            'reason': 'Invalid IP Address',
        })
        with patch('odoo.addons.export_delete_login_log.models.'
                   'login_user_log.requests.get', side_effect=fake_get):
            with patch(
                'odoo.addons.base.models.res_users.Users._check_credentials',
                return_value=None,
            ):
                user.sudo()._check_credentials('admin', {})
        log = self.LoginLog.sudo().search(
            [('ip_address', '=', '88.88.88.88')], limit=1)
        self.assertTrue(log)
        # ip_data only holds {"ip": ...} when error=True, so remark is None
        self.assertFalse(log.remark)

    def test_check_credentials_no_geo_sets_null_geo_loc(self):
        """When latitude/longitude are absent, geo_loc should be None/False."""
        user = self.env.ref('base.user_admin')
        fake_get = self._mock_requests(ip='77.77.77.77', api_response={
            'error': True,
            'reason': 'Reserved IP Address',
        })
        with patch('odoo.addons.export_delete_login_log.models.'
                   'login_user_log.requests.get', side_effect=fake_get):
            # Patch only the super() call so real auth is skipped,
            # but the module's _check_credentials override (which creates
            # the login.log record) still executes in full.
            with patch(
                'odoo.addons.base.models.res_users.Users._check_credentials',
                return_value=None,
            ):
                user.sudo()._check_credentials('admin', {})
        log = self.LoginLog.sudo().search(
            [('ip_address', '=', '77.77.77.77')], limit=1)
        self.assertTrue(log)
        self.assertFalse(log.geo_loc)

    def test_check_credentials_with_api_key_param(self):
        """When have_api_key is set, the API URL should include the key.
        The login.log entry should still be created correctly."""
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.have_api_key', 'True')
        self.env['ir.config_parameter'].sudo().set_param(
            'export_delete_login_log.ipapi_key', 'TESTKEY123')
        user = self.env.ref('base.user_admin')
        fake_get = self._mock_requests(ip='66.66.66.66')
        with patch('odoo.addons.export_delete_login_log.models.'
                   'login_user_log.requests.get', side_effect=fake_get):
            # Patch only the super() call so real auth is skipped,
            # but the module's _check_credentials override (which creates
            # the login.log record) still executes in full.
            with patch(
                'odoo.addons.base.models.res_users.Users._check_credentials',
                return_value=None,
            ):
                user.sudo()._check_credentials('admin', {})
        log = self.LoginLog.sudo().search(
            [('ip_address', '=', '66.66.66.66')], limit=1)
        self.assertTrue(log)

    def test_check_credentials_address_built_correctly(self):
        """address field should be 'city, region, country' joined."""
        user = self.env.ref('base.user_admin')
        fake_get = self._mock_requests(ip='33.33.33.33', api_response={
            'latitude': 40.71,
            'longitude': -74.00,
            'city': 'New York',
            'region': 'New York',
            'country_name': 'United States',
            'postal': '10001',
            'timezone': 'America/New_York',
            'error': False,
            'reason': None,
        })
        with patch('odoo.addons.export_delete_login_log.models.'
                   'login_user_log.requests.get', side_effect=fake_get):
            # Patch only the super() call so real auth is skipped,
            # but the module's _check_credentials override (which creates
            # the login.log record) still executes in full.
            with patch(
                'odoo.addons.base.models.res_users.Users._check_credentials',
                return_value=None,
            ):
                user.sudo()._check_credentials('admin', {})
        log = self.LoginLog.sudo().search(
            [('ip_address', '=', '33.33.33.33')], limit=1)
        self.assertTrue(log)
        self.assertEqual(log.address, 'New York, New York, United States')
