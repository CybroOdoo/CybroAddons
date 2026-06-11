# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (<https://www.cybrosys.com>)
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

from odoo.tests import HttpCase, tagged
import base64


@tagged('post_install', '-at_install')
class TestUserLog(HttpCase):
    """Test case for the Login User Info module."""

    def setUp(self):
        super().setUp()
        self.login = 'admin'
        self.password = 'admin'
        self.dummy_image = base64.b64encode(b'dummy_image_data')

    def test_01_successful_login_log(self):
        """Test if a user log record is created on successful login with an image."""
        log_count_before = self.env['user.log'].search_count([])

        response = self.url_open('/web/login')
        csrf_token = self.extract_csrf_token(response.text)

        data = {
            'login': self.login,
            'password': self.password,
            'captured_image': self.dummy_image.decode('utf-8'),
            'csrf_token': csrf_token,
        }
        self.url_open('/web/login', data=data)

        log_count_after = self.env['user.log'].search_count([])
        self.assertEqual(
            log_count_after,
            log_count_before + 1,
            "A user log should be created on successful login."
        )

        last_log = self.env['user.log'].search(
            [], order='create_date desc', limit=1
        )
        admin_user = self.env['res.users'].search(
            [('login', '=', self.login)], limit=1
        )

        self.assertEqual(
            last_log.user_id,
            admin_user,
            "The log record should be associated with the correct user."
        )
        self.assertEqual(
            last_log.image,
            self.dummy_image,
            "The captured image should be saved correctly."
        )
        self.assertFalse(
            last_log.is_secure,
            "is_secure should be False for a successful login."
        )

    def test_02_failed_login_log(self):
        """Test if a user log record is created on failed login with an image."""
        log_count_before = self.env['user.log'].search_count([])

        response = self.url_open('/web/login')
        csrf_token = self.extract_csrf_token(response.text)

        data = {
            'login': 'wrong_user',
            'password': 'wrong_password',
            'captured_image': self.dummy_image.decode('utf-8'),
            'csrf_token': csrf_token,
        }
        self.url_open('/web/login', data=data)

        log_count_after = self.env['user.log'].search_count([])
        self.assertEqual(
            log_count_after,
            log_count_before + 1,
            "A user log should be created even on failed login."
        )

        last_log = self.env['user.log'].search(
            [], order='create_date desc', limit=1
        )

        self.assertFalse(
            last_log.user_id,
            "The log record should not have a user_id for a failed login attempt."
        )
        self.assertEqual(
            last_log.image,
            self.dummy_image,
            "The captured image should be saved correctly."
        )
        self.assertTrue(
            last_log.is_secure,
            "is_secure should be True for a failed login."
        )

    def extract_csrf_token(self, html):
        """Helper to extract CSRF token from HTML."""
        import re

        match = re.search(r'name="csrf_token" value="(.+?)"', html)
        return match.group(1) if match else None
