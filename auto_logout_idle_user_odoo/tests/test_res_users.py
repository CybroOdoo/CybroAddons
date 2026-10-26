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

from odoo.exceptions import ValidationError
from odoo.http.session import session_store
from odoo.tests.common import (
    HttpCase,
    JsonRpcException,
    TransactionCase,
    new_test_user,
    tagged,
)

from odoo.addons.auto_logout_idle_user_odoo.controllers.auto_logout_idle_user_odoo import (
    AutoLogoutIdleUser,
)

IDLE_URL = '/auto_logout_idle_user_odoo/idle_time'


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):

    def test_default_idle_time(self):
        """The default idle time is 15 minutes."""
        user = new_test_user(self.env, login='idle_default_user')
        self.assertEqual(user.idle_time, 15.0)
        self.assertFalse(user.enable_idle)

    def test_update_user_valid_idle_time(self):
        """Test updating a user with a valid idle time"""
        user = self.env.user
        user.write({
            'enable_idle': True,
            'idle_time': 15.0,
        })
        self.assertEqual(user.idle_time, 15.0, "Idle time should be set correctly.")
        self.assertTrue(user.enable_idle, "Enable idle should be True.")

    def test_update_user_minimum_idle_time(self):
        """Exactly one minute is accepted when enabled."""
        user = self.env.user
        user.write({'enable_idle': True, 'idle_time': 1.0})
        self.assertEqual(user.idle_time, 1.0)

    def test_update_user_invalid_idle_time(self):
        """Test updating a user with an invalid idle time (<= 0) when enabled"""
        user = self.env.user
        with self.assertRaises(ValidationError):
            user.write({'enable_idle': True, 'idle_time': 0})

    def test_update_user_too_small_idle_time(self):
        """Less than one minute is rejected when enabled."""
        user = self.env.user
        with self.assertRaises(ValidationError):
            user.write({'enable_idle': True, 'idle_time': 0.5})

    def test_update_user_negative_idle_time(self):
        """Test updating a user with a negative idle time when enabled"""
        user = self.env.user
        with self.assertRaises(ValidationError):
            user.write({'enable_idle': True, 'idle_time': -5})

    def test_update_user_disabled_idle_time(self):
        """Test user can have 0 idle time when enable_idle is False"""
        user = self.env.user
        user.write({'enable_idle': False, 'idle_time': 0})
        self.assertEqual(user.idle_time, 0)
        self.assertFalse(user.enable_idle)

    def test_controller_get_idle_time(self):
        """The timer endpoint returns the idle time only when enabled."""
        func = getattr(AutoLogoutIdleUser.get_idle_time, 'original_endpoint', AutoLogoutIdleUser.get_idle_time)
        user = self.env.user
        user.write({'enable_idle': True, 'idle_time': 12.0})
        target = 'odoo.addons.auto_logout_idle_user_odoo.controllers.auto_logout_idle_user_odoo.request'
        with patch(target, new=MagicMock(env=MagicMock(user=user))):
            self.assertEqual(func(AutoLogoutIdleUser()), {'idle_time': 12.0})
            user.write({'enable_idle': False})
            self.assertEqual(func(AutoLogoutIdleUser()), {'idle_time': 0})


@tagged('post_install', '-at_install')
class TestAutoLogoutHttp(HttpCase):
    """Test suite covering the HTTP endpoint and session logout behavior."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.idle_user = new_test_user(
            cls.env,
            login='idle_test_user',
            password='TestPassword123!',
            name='Idle Test User',
            groups='base.group_user',
            enable_idle=True,
            idle_time=10.0,
        )
        cls.normal_user = new_test_user(
            cls.env,
            login='normal_test_user',
            password='TestPassword123!',
            name='Normal Test User',
            groups='base.group_user',
            enable_idle=False,
            idle_time=1.0,
        )

    def test_idle_user_timer_and_session_logout(self):
        """Authenticate user, verify timer endpoint, then execute the logout flow."""
        auth_session = self.authenticate(self.idle_user.login, 'TestPassword123!')
        sid = auth_session.sid
        self.assertTrue(session_store().get(sid), "Session should exist after login.")

        # Test controller returns configured idle minutes
        data = self.make_jsonrpc_request(IDLE_URL, {})
        self.assertEqual(data, {'idle_time': 10.0}, "Endpoint should return user's idle time.")

        # Simulate systray countdown expiration calling /web/session/logout
        csrf_token = self.csrf_token()
        logout_response = self.url_open(
            '/web/session/logout',
            method='POST',
            data={'csrf_token': csrf_token},
            allow_redirects=False,
        )
        self.assertEqual(logout_response.status_code, 303, "Logout should return a redirect.")
        redirect_url = logout_response.headers.get('Location', '')
        self.assertTrue(redirect_url, "Logout must provide a redirect URL.")

        # Session must be terminated in the session store
        self.assertFalse(session_store().get(sid), "Session must be destroyed after logout.")

        # Subsequent authenticated endpoint call should fail because user is logged out
        with self.assertRaises(JsonRpcException):
            self.make_jsonrpc_request(IDLE_URL, {})

    def test_disabled_idle_user_timer(self):
        """When idle logout is disabled, the endpoint reports no timeout."""
        self.authenticate(self.normal_user.login, 'TestPassword123!')
        self.assertEqual(self.session.uid, self.normal_user.id)

        data = self.make_jsonrpc_request(IDLE_URL, {})
        self.assertEqual(data, {'idle_time': 0}, "Endpoint should report no timeout when disabled.")
        self.assertEqual(self.session.uid, self.normal_user.id, "Session should remain active.")
