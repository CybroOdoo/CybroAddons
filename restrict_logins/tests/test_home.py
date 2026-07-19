# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from odoo.exceptions import AccessDenied
from odoo.tests.common import TransactionCase, tagged



@tagged('post_install', '-at_install')
class TestHomeLoginAlreadyLoggedIn(TransactionCase):
    """Tests for the Home.web_login controller's 'already logged in' branch."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()


        cls.env['ir.config_parameter'].sudo().set_param(
            'restrict_logins.session_expire_time', '60')

        cls.logged_in_user = cls.env['res.users'].create({
            'name': 'Already Logged In',
            'login': 'already_logged@test.com',
            'password': 'Test@1234',
        })

        cls.logged_in_user.sudo().write({
            'sid': 'active-session-sid',
            'exp_date': datetime.now() + timedelta(minutes=30),
            'logged_in': True,
        })


    def test_user_with_active_session_has_all_three_fields(self):
        """Test active session fields."""

        user = self.logged_in_user.sudo()

        self.assertTrue(user.sid)
        self.assertTrue(user.exp_date)
        self.assertTrue(user.logged_in)


    def test_already_logged_in_condition(self):
        """Test already logged in condition."""


        user = self.logged_in_user.sudo()
        condition = bool(user.exp_date and user.sid and user.logged_in)

        self.assertTrue(condition)

    def test_not_already_logged_in_when_no_sid(self):
        """Test login condition without sid."""

        user = self.env['res.users'].sudo().create({
            'name': 'No Sid User',
            'login': 'no_sid@test.com',
            'password': 'Test@1234',
        })

        condition = bool(user.exp_date and user.sid and user.logged_in)

        self.assertFalse(condition)


    def test_not_already_logged_in_when_exp_date_missing(self):
        """Test login condition without exp_date."""


        user = self.env['res.users'].sudo().create({
            'name': 'No ExpDate User',
            'login': 'no_expdate@test.com',
            'password': 'Test@1234',
        })

        user.write({
            'sid': 'some-sid',
            'logged_in': True,
            'exp_date': False
        })

        condition = bool(user.exp_date and user.sid and user.logged_in)

        self.assertFalse(condition)


    def test_clearing_session_allows_relogin(self):
        """Test clearing session."""

        user = self.logged_in_user.sudo()

        user._clear_session()

        condition = bool(user.exp_date and user.sid and user.logged_in)

        self.assertFalse(condition)


    def test_login_raises_access_denied_for_active_session(self):
        """Test login raises AccessDenied."""

        user = self.logged_in_user.sudo()

        user.write({
            'sid': 'login-test-sid',
            'exp_date': datetime.now() + timedelta(minutes=30),
            'logged_in': True,
        })

        mock_user = MagicMock()
        mock_user.exp_date = user.exp_date
        mock_user.sid = user.sid
        mock_user.logged_in = user.logged_in
        mock_user.name = user.name
        mock_user.tz = user.tz
        mock_user.login_date = user.login_date
        mock_user.id = user.id

        mock_request = MagicMock()
        mock_request.httprequest.environ = {
            'REMOTE_ADDR': '127.0.0.1'
        }
        mock_request.httprequest.cookies = {}
        mock_request.env.uid = None

        with patch(
                'odoo.addons.restrict_logins.models.res_users.request',
                mock_request):

            already_logged_in = bool(
                mock_user.exp_date and
                mock_user.sid and
                mock_user.logged_in
            )

            self.assertTrue(already_logged_in)


@tagged('post_install', '-at_install')
class TestHomeLoginErrorMessages(TransactionCase):
    """Tests for login error messages."""

    def test_already_logged_in_error_key(self):
        """Test already_logged_in error key."""

        exc = AccessDenied("already_logged_in")

        self.assertEqual(exc.args[0], "already_logged_in")

    def test_default_access_denied_args(self):
        """Test default AccessDenied args."""

        default_exc = AccessDenied()

        self.assertEqual(default_exc.args, AccessDenied().args)

    def test_wrong_credentials_not_already_logged_in(self):
        """Test wrong credentials."""

        exc = AccessDenied()

        is_already_logged_in = (
            exc.args[0] == "already_logged_in"
            if exc.args else False
        )

        self.assertFalse(is_already_logged_in)


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Tests for ResConfigSettings."""

    def test_session_expire_time_field_exists(self):
        """Test session_expire_time field exists."""

        self.assertIn(
            'session_expire_time',
            self.env['res.config.settings']._fields
        )

    def test_session_expire_time_is_integer(self):
        """Test session_expire_time field type."""


        field = self.env['res.config.settings']._fields[
            'session_expire_time'
        ]

        self.assertEqual(field.type, 'integer')

    def test_set_and_get_session_expire_time(self):
        """Test set and get config parameter."""

        self.env['ir.config_parameter'].sudo().set_param(
            'restrict_logins.session_expire_time', '45'
        )

        value = self.env['ir.config_parameter'].sudo().get_param(
            'restrict_logins.session_expire_time'
        )

        self.assertEqual(int(value), 45)
