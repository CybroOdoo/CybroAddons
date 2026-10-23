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

from odoo import SUPERUSER_ID
from odoo.exceptions import AccessDenied, AccessError
from odoo.http.session import Session
from odoo.tests.common import TransactionCase, new_test_user, tagged

from odoo.addons.login_using_qr import post_init_hook
from odoo.addons.login_using_qr.controllers.authenticate import (
    authenticate_without_passwd,
)
from odoo.addons.login_using_qr.controllers.login_using_qr import LoginController


@tagged('post_install', '-at_install')
class TestLoginUsingQR(TransactionCase):
    """Test suite for QR code generation, security, and authentication."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = new_test_user(
            cls.env,
            login='qr_test_user',
            password='TestPassword123!',
            name='QR Test User',
            groups='base.group_user',
        )

    def test_qr_token_generated_on_creation(self):
        """Test that a new user automatically gets an indexable QR token."""
        self.assertTrue(self.test_user.qr_token)
        self.assertGreater(len(self.test_user.qr_token), 20)

    def test_new_users_get_distinct_tokens(self):
        """Users created together each get their own token."""
        users = self.env['res.users'].create([
            {'name': f'QR Bulk {index}', 'login': f'qr_bulk_{index}'}
            for index in range(3)
        ])
        tokens = users.sudo().mapped('qr_token')
        self.assertEqual(len(set(tokens)), 3)
        self.assertTrue(all(tokens))

    def test_post_init_hook_gives_distinct_tokens(self):
        """Existing internal users without a token each get their own token."""
        users = self.test_user | new_test_user(
            self.env, login='qr_hook_user', groups='base.group_user')
        self.env.cr.execute(
            "UPDATE res_users SET qr_token = NULL WHERE id IN %s", (tuple(users.ids),))
        users.invalidate_recordset()
        post_init_hook(self.env(user=SUPERUSER_ID))
        tokens = users.sudo().mapped('qr_token')
        self.assertTrue(all(tokens))
        self.assertEqual(len(set(tokens)), len(users))

    def test_action_regenerate_qr_token(self):
        """Test regenerating QR token assigns a new unique token and updates QR code."""
        initial_token = self.test_user.qr_token
        self.test_user.action_regenerate_qr_token()
        new_token = self.test_user.qr_token

        self.assertTrue(new_token)
        self.assertNotEqual(initial_token, new_token)

    def test_qr_code_binary_computed(self):
        """Test that qr_code binary is computed from the qr_token."""
        self.assertTrue(self.test_user.qr_code)

    def test_qr_token_uniqueness(self):
        """Test that two different users receive different QR tokens."""
        other_user = new_test_user(
            self.env,
            login='qr_other_user',
            password='TestPassword123!',
            name='QR Other User',
            groups='base.group_user',
        )
        self.assertNotEqual(self.test_user.qr_token, other_user.qr_token)

    def test_security_field_groups_restriction(self):
        """Test that non-admin users cannot read qr_token or qr_code of other users."""
        non_admin = new_test_user(
            self.env,
            login='regular_employee_user',
            password='TestPassword123!',
            name='Regular Employee',
            groups='base.group_user',
        )
        user_as_non_admin = self.test_user.with_user(non_admin)
        # Reading qr_token and qr_code via non-admin environment must raise AccessError
        # because the fields are restricted with groups='base.group_system'
        with self.assertRaises(AccessError):
            user_as_non_admin.read(['qr_token'])
        with self.assertRaises(AccessError):
            user_as_non_admin.read(['qr_code'])

    def test_compute_qr_code_handles_missing_library(self):
        """Test that _compute_qr_code gracefully handles missing qrcode library without raising UserError."""
        with patch('odoo.addons.login_using_qr.models.res_users.qrcode', None):
            self.test_user._compute_qr_code()
            self.assertFalse(self.test_user.qr_code)

    def test_controller_scanner_invalid_inputs(self):
        """Test controller handles invalid, empty, or short QR strings."""
        controller = LoginController()

        # None or non-string
        self.assertFalse(controller.scanner(None))
        self.assertFalse(controller.scanner(12345))

        # Too short string
        self.assertFalse(controller.scanner("abc"))

    def test_controller_scanner_flow(self):
        """Test controller scanning token, verifying 2FA check and authenticating."""
        controller = LoginController()

        mock_session = MagicMock()
        mock_session.db = self.env.cr.dbname

        with patch('odoo.addons.login_using_qr.controllers.login_using_qr.request', new=MagicMock()) as mock_req, \
                patch('odoo.addons.login_using_qr.controllers.login_using_qr.authenticate_without_passwd') as mock_auth:
            mock_req.session = mock_session
            mock_req.env = self.env
            mock_req.db = self.env.cr.dbname

            # Valid QR token authenticates correct user
            res = controller.scanner(self.test_user.qr_token)
            self.assertTrue(res)
            mock_auth.assert_called_once_with(mock_session, self.env.cr.dbname, self.test_user.login)

            # Different user's QR token authenticates that specific user, not test_user
            mock_auth.reset_mock()
            second_user = new_test_user(
                self.env,
                login='qr_second_user',
                password='TestPassword123!',
                name='QR Second User',
                groups='base.group_user',
            )
            res_second = controller.scanner(second_user.qr_token)
            self.assertTrue(res_second)
            mock_auth.assert_called_once_with(mock_session, self.env.cr.dbname, second_user.login)

            # Unknown QR token
            res_unknown = controller.scanner("nonexistent_random_token_123456789")
            self.assertFalse(res_unknown)

            # 2FA enabled user should be rejected to prevent 2FA bypass
            user_2fa = new_test_user(
                self.env,
                login='qr_2fa_user',
                password='TestPassword123!',
                name='QR 2FA User',
                groups='base.group_user',
            )
            # totp_enabled only exists when auth_totp is installed, so the
            # attribute is patched on the model class to keep the test independent
            with patch.object(type(self.env['res.users']), 'totp_enabled', True, create=True):
                res_2fa = controller.scanner(user_2fa.qr_token)
            self.assertFalse(res_2fa)

            # Error during authentication
            mock_auth.side_effect = AccessDenied()
            res_error = controller.scanner(self.test_user.qr_token)
            self.assertFalse(res_error)

    def test_authenticate_without_passwd_method(self):
        """Test standalone authenticate_without_passwd behavior on valid and invalid users."""
        session = Session({}, 'a' * 84)

        registry = MagicMock()
        registry.cursor.return_value.__enter__.return_value = self.env.cr
        registry.cursor.return_value.__exit__.return_value = False
        with patch('odoo.addons.login_using_qr.controllers.authenticate.Registry', return_value=registry), \
                patch('odoo.addons.login_using_qr.controllers.authenticate.finalize') as mock_finalize:
            # Valid user
            authenticate_without_passwd(session, self.env.cr.dbname, self.test_user.login)
            self.assertEqual(session.get('pre_login'), self.test_user.login)
            self.assertEqual(session.get('pre_uid'), self.test_user.id)
            mock_finalize.assert_called_once()

            # Invalid user raises Exception
            with self.assertRaises(AccessDenied):
                authenticate_without_passwd(session, self.env.cr.dbname, "nonexistent_login_xyz")
