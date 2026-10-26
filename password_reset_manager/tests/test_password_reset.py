# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import re
from unittest.mock import patch

from odoo.tests import HttpCase, tagged
from odoo.tools import config

from odoo.addons.password_reset_manager.controllers import utils

CHANGE_URL = '/web/reset_password/submit'
MASTER_URL = '/web/reset_by_master_pass/submit'


@tagged('post_install', '-at_install')
class TestPasswordResetManager(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].create({
            'name': 'Reset Tester',
            'login': 'reset_tester',
            'password': 'Old-Passw0rd!x',
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def setUp(self):
        super().setUp()
        utils._failed_attempts.clear()
        self.addCleanup(utils._failed_attempts.clear)
        self._set_reset_enabled(True)

    def _set_reset_enabled(self, enabled):
        params = self.env['ir.config_parameter'].sudo()
        key = 'auth_signup.reset_password'
        value = 'True' if enabled else 'False'
        record = params.search([('key', '=', key)], limit=1)
        if record:
            record.value = value
        else:
            params.create({'key': key, 'value': value})
        self.env.flush_all()

    def _csrf(self, url):
        """Load a form page and return its CSRF token."""
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
        self.assertTrue(match, "The form must contain a CSRF token.")
        return match.group(1)

    def _post_change(self, **data):
        data.setdefault('csrf_token', self._csrf('/web/reset_password/direct'))
        return self.url_open(CHANGE_URL, data=data, allow_redirects=False)

    def _post_master(self, **data):
        data.setdefault('csrf_token', self._csrf('/web/forgot_password'))
        return self.url_open(MASTER_URL, data=data, allow_redirects=False)

    # ---- pages are only reachable when the option is enabled ----
    def test_01_pages_follow_settings(self):
        for url in ('/web/forgot_password', '/web/reset_password/direct'):
            self.assertEqual(self.url_open(url).status_code, 200)
        self._set_reset_enabled(False)
        for url in ('/web/forgot_password', '/web/reset_password/direct'):
            self.assertEqual(self.url_open(url).status_code, 404)

    def test_02_submit_routes_disabled(self):
        token = self._csrf('/web/reset_password/direct')
        self._set_reset_enabled(False)
        for url in (CHANGE_URL, MASTER_URL):
            response = self.url_open(
                url, data={'csrf_token': token}, allow_redirects=False)
            self.assertEqual(response.status_code, 404)

    def test_03_csrf_is_enforced(self):
        response = self.url_open(
            CHANGE_URL, data={'user_name': 'reset_tester'},
            allow_redirects=False)
        self.assertEqual(response.status_code, 400)

    # ---- change password with the old password ----
    def test_04_missing_fields_no_server_error(self):
        response = self._post_change(user_name='reset_tester')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Please fill in all the fields.', response.text)

    def test_05_passwords_do_not_match(self):
        response = self._post_change(
            user_name='reset_tester', old_password='Old-Passw0rd!x',
            new_password='New-Passw0rd!x', confirm_new_password='other')
        self.assertIn('The passwords do not match.', response.text)

    def test_06_wrong_old_password(self):
        response = self._post_change(
            user_name='reset_tester', old_password='wrong',
            new_password='New-Passw0rd!x',
            confirm_new_password='New-Passw0rd!x')
        self.assertIn('Login or password is incorrect.', response.text)

    def test_07_change_password_success(self):
        response = self._post_change(
            user_name='reset_tester', old_password='Old-Passw0rd!x',
            new_password='New-Passw0rd!x',
            confirm_new_password='New-Passw0rd!x')
        self.assertIn(response.status_code, (302, 303))
        self.assertIn('/web/login', response.headers['Location'])

    def test_08_change_password_throttled(self):
        for _i in range(utils.MAX_FAILED_ATTEMPTS):
            self._post_change(
                user_name='reset_tester', old_password='wrong',
                new_password='a', confirm_new_password='a')
        response = self._post_change(
            user_name='reset_tester', old_password='Old-Passw0rd!x',
            new_password='a', confirm_new_password='a')
        self.assertIn('Too many failed attempts.', response.text)

    # ---- reset password with the master password ----
    def test_09_master_missing_and_mismatch(self):
        response = self._post_master(user_name='reset_tester')
        self.assertIn('Please fill in all the fields.', response.text)
        response = self._post_master(
            user_name='reset_tester', master_password='secret',
            new_password='a', confirm_new_password='b')
        self.assertIn('The passwords do not match.', response.text)

    def test_10_master_password_flow(self):
        with patch.object(config, 'verify_admin_password',
                          side_effect=lambda pwd: pwd == 'secret'):
            response = self._post_master(
                user_name='reset_tester', master_password='bad',
                new_password='New-Passw0rd!x',
                confirm_new_password='New-Passw0rd!x')
            self.assertIn('The master password is incorrect.', response.text)
            response = self._post_master(
                user_name='unknown_user', master_password='secret',
                new_password='New-Passw0rd!x',
                confirm_new_password='New-Passw0rd!x')
            self.assertIn('The user name is not valid.', response.text)
            response = self._post_master(
                user_name='reset_tester', master_password='secret',
                new_password='New-Passw0rd!x',
                confirm_new_password='New-Passw0rd!x')
            self.assertIn(response.status_code, (302, 303))
            self.assertIn('/web/login', response.headers['Location'])

    def test_11_master_password_throttled(self):
        with patch.object(config, 'verify_admin_password',
                          return_value=False):
            for _i in range(utils.MAX_FAILED_ATTEMPTS):
                self._post_master(
                    user_name='reset_tester', master_password='bad',
                    new_password='a', confirm_new_password='a')
            response = self._post_master(
                user_name='reset_tester', master_password='bad',
                new_password='a', confirm_new_password='a')
        self.assertIn('Too many failed attempts.', response.text)
