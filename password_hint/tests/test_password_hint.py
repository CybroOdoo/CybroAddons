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
from unittest.mock import patch

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPasswordHintModel(TransactionCase):
    """Unit tests for the password_hint field on res.users model."""

    def test_create_user_with_hint(self):
        """Verify that password_hint is correctly stored on user creation."""
        user = self.env['res.users'].create({
            'name': 'Hint Test User',
            'login': 'hint_test_create@example.com',
            'password_hint': 'First car was a Beetle',
        })
        self.assertEqual(
            user.password_hint,
            'First car was a Beetle',
            "Password hint should be stored correctly on user record."
        )

    def test_update_user_hint(self):
        """Verify that updating password_hint persists the new value."""
        user = self.env['res.users'].create({
            'name': 'Hint Update User',
            'login': 'hint_test_update@example.com',
            'password_hint': 'Old hint',
        })
        user.write({'password_hint': 'New hint'})
        self.assertEqual(
            user.password_hint,
            'New hint',
            "Password hint should be updated successfully."
        )

    def test_user_without_hint(self):
        """Verify that password_hint is False if not set."""
        user = self.env['res.users'].create({
            'name': 'No Hint User',
            'login': 'no_hint@example.com',
        })
        self.assertFalse(
            user.password_hint,
            "Password hint should be False when not provided."
        )


@tagged('post_install', '-at_install')
class TestPasswordHintController(HttpCase):
    """Integration and HTTP tests for Password Hint controllers and views."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        portal_group = cls.env.ref('base.group_portal')
        cls.user_with_hint = cls.env['res.users'].create({
            'name': 'User With Hint',
            'login': 'user_with_hint@example.com',
            'password_hint': 'Mother maiden name is Smith',
            'group_ids': [portal_group.id],
        })
        cls.user_without_hint = cls.env['res.users'].create({
            'name': 'User Without Hint',
            'login': 'user_without_hint@example.com',
            'group_ids': [portal_group.id],
        })
        # Internal / admin user to test that hints are never disclosed for non-portal users
        cls.internal_user = cls.env['res.users'].create({
            'name': 'Internal Admin User',
            'login': 'internal_admin@example.com',
            'password_hint': 'SecretAdminHint',
        })

    def test_rpc_get_hint_success(self):
        """Verify JSON-RPC endpoint returns password hint for valid portal user."""
        response = self.make_jsonrpc_request(
            '/website/password/hint',
            {'login': 'user_with_hint@example.com'}
        )
        self.assertEqual(
            response,
            'Mother maiden name is Smith',
            "Controller should return the correct password hint for portal users."
        )

    def test_rpc_get_hint_internal_user_denied(self):
        """Verify JSON-RPC endpoint returns False for internal/admin users."""
        response = self.make_jsonrpc_request(
            '/website/password/hint',
            {'login': 'internal_admin@example.com'}
        )
        self.assertFalse(
            response,
            "Controller should return False for internal users to prevent credential disclosure."
        )

    def test_rpc_get_hint_empty_when_no_hint(self):
        """Verify JSON-RPC endpoint returns False when user has no hint."""
        response = self.make_jsonrpc_request(
            '/website/password/hint',
            {'login': 'user_without_hint@example.com'}
        )
        self.assertFalse(
            response,
            "Controller should return False when user has no password hint."
        )

    def test_rpc_get_hint_nonexistent_user(self):
        """Verify JSON-RPC endpoint returns False for unknown login."""
        response = self.make_jsonrpc_request(
            '/website/password/hint',
            {'login': 'nonexistent_user_999@example.com'}
        )
        self.assertFalse(
            response,
            "Controller should return False for non-existent user."
        )

    def test_rpc_get_hint_without_login_param(self):
        """Verify JSON-RPC endpoint returns False when login is empty/missing."""
        response = self.make_jsonrpc_request(
            '/website/password/hint',
            {}
        )
        self.assertFalse(
            response,
            "Controller should return False when no login parameter is provided."
        )

    def test_login_page_contains_hint_button(self):
        """Verify that the login page template contains the Password Hint button."""
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'id="Password_login_hint"',
            response.text,
            "The Password Hint button should be rendered on the login page."
        )

    def test_signup_page_contains_hint_field(self):
        """Verify that the signup page template contains the password hint input field."""
        # Enable free signup in settings
        self.env['ir.config_parameter'].sudo().set_str('auth_signup.invitation_scope', 'b2c')
        response = self.url_open('/web/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'name="hint"',
            response.text,
            "The password hint input field should be present in the signup form."
        )

    def test_signup_get_does_not_overwrite_hint(self):
        """Security test: GET request to signup must never overwrite an existing user's hint."""
        self.url_open('/web/signup?token=dummy_token&login=user_with_hint@example.com&hint=MaliciousAttempt')
        self.user_with_hint.invalidate_recordset(['password_hint'])
        self.assertEqual(
            self.user_with_hint.password_hint,
            'Mother maiden name is Smith',
            "GET request to /web/signup must not overwrite existing user's password hint."
        )

    @patch('odoo.addons.auth_signup.controllers.main.AuthSignupHome._prepare_signup_values', return_value={'name': 'Test User', 'login': 'test_prep@example.com'})
    def test_prepare_signup_values_includes_hint(self, mock_super):
        """Verify that _prepare_signup_values includes password_hint in returned dictionary."""
        from odoo.addons.password_hint.controllers.password_hint import PasswordHint
        controller = PasswordHint()
        qcontext = {
            'name': 'Test User',
            'login': 'test_prep@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'hint': 'Security Hint 123',
        }
        values = controller._prepare_signup_values(qcontext)
        self.assertEqual(
            values.get('password_hint'),
            'Security Hint 123',
            "_prepare_signup_values should include password_hint."
        )
