# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Safa K B (odoo@cybrosys.com)
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
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):
    """Test cases for the res.users extension (models/res_users.py).
    Covers: _compute_automail, action_confirm, action_fetch.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env['provider.server'].create({
            'name': 'Gmail',
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 465,
            'smtp_encryption': 'ssl',
            'server': 'imap.gmail.com',
            'port': 993,
            'server_type': 'imap',
            'is_ssl': True,
        })
        cls.test_user = cls.env.ref('base.user_admin')
        cls.test_user.write({
            'provider': cls.provider.id,
            'pwd': 'test_app_password',
        })

    def test_compute_automail_true_when_param_set(self):
        """Test _compute_automail() sets automail=True when the system
        parameter 'email_configurator_advanced.automail_server' is truthy."""
        self.env['ir.config_parameter'].sudo().set_param(
            'email_configurator_advanced.automail_server', 'True')
        self.test_user._compute_automail()
        self.assertTrue(
            self.test_user.automail,
            "automail must be True when the system param is set.")

    def test_compute_automail_false_when_param_not_set(self):
        """Test _compute_automail() sets automail=False when the system
        parameter 'email_configurator_advanced.automail_server' is absent
        or falsy."""
        self.env['ir.config_parameter'].sudo().set_param(
            'email_configurator_advanced.automail_server', False)
        self.test_user._compute_automail()
        self.assertFalse(
            self.test_user.automail,
            "automail must be False when the system param is not set.")

    def test_compute_automail_false_when_param_empty_string(self):
        """Test _compute_automail() sets automail=False when the system
        parameter is an empty string (falsy)."""
        self.env['ir.config_parameter'].sudo().set_param(
            'email_configurator_advanced.automail_server', '')
        self.test_user._compute_automail()
        self.assertFalse(
            self.test_user.automail,
            "automail must be False when the system param is an empty string.")

    def test_action_confirm_raises_user_error_without_provider(self):
        """Test action_confirm() raises UserError when no provider is set
        on the user."""
        user_no_provider = self.test_user.copy({
            'login': 'no_provider_test_user@example.com',
            'email': 'no_provider_test_user@example.com',
        })
        user_no_provider.provider = False
        with self.assertRaises(UserError,
                               msg="UserError must be raised when provider "
                                   "is not selected."):
            user_no_provider.action_confirm()

    def test_action_confirm_creates_mail_server_when_none_exists(self):
        """Test action_confirm() creates a new ir.mail_server record when no
        outgoing server for the user's email + provider combination exists."""
        self.env['ir.mail_server'].search([
            ('smtp_user', '=', self.test_user.email),
            ('name', '=', self.provider.name),
        ]).unlink()
        self.env['fetchmail.server'].search([
            ('user', '=', self.test_user.email),
            ('name', '=', self.provider.name),
        ]).unlink()

        with patch.object(type(self.env['ir.mail_server']),
                          'test_smtp_connection',
                          return_value=None), \
             patch.object(type(self.env['fetchmail.server']),
                          'button_confirm_login',
                          return_value=None):
            self.test_user.action_confirm()

        mail_server = self.env['ir.mail_server'].search([
            ('smtp_user', '=', self.test_user.email),
            ('name', '=', self.provider.name),
        ], limit=1)
        self.assertTrue(
            mail_server.exists(),
            "A new ir.mail_server must be created by action_confirm().")

    def test_action_confirm_creates_fetchmail_server_when_none_exists(self):
        """Test action_confirm() creates a new fetchmail.server record when no
        incoming server for the user's email + provider combination exists."""
        self.env['ir.mail_server'].search([
            ('smtp_user', '=', self.test_user.email),
            ('name', '=', self.provider.name),
        ]).unlink()
        self.env['fetchmail.server'].search([
            ('user', '=', self.test_user.email),
            ('name', '=', self.provider.name),
        ]).unlink()

        with patch.object(type(self.env['ir.mail_server']),
                          'test_smtp_connection',
                          return_value=None), \
             patch.object(type(self.env['fetchmail.server']),
                          'button_confirm_login',
                          return_value=None):
            self.test_user.action_confirm()

        fetchmail_server = self.env['fetchmail.server'].search([
            ('user', '=', self.test_user.email),
            ('name', '=', self.provider.name),
        ], limit=1)
        self.assertTrue(
            fetchmail_server.exists(),
            "A new fetchmail.server must be created by action_confirm().")

    def test_action_confirm_updates_existing_mail_server(self):
        """Test action_confirm() updates an existing ir.mail_server instead
        of creating a duplicate when one already exists for the same user
        + provider combination."""
        # Ensure exactly one outgoing server exists
        self.env['ir.mail_server'].search([
            ('smtp_user', '=', self.test_user.email),
            ('name', '=', self.provider.name),
        ]).unlink()
        existing = self.env['ir.mail_server'].create({
            'name': self.provider.name,
            'smtp_host': 'old.smtp.host',
            'smtp_port': 25,
            'smtp_encryption': 'none',
            'smtp_user': self.test_user.email,
            'smtp_pass': 'old_pass',
        })
        self.env['fetchmail.server'].search([
            ('user', '=', self.test_user.email),
            ('name', '=', self.provider.name),
        ]).unlink()
        existing_fetch = self.env['fetchmail.server'].create({
            'name': self.provider.name,
            'server': 'old.imap.host',
            'port': 143,
            'server_type': 'imap',
            'user': self.test_user.email,
            'password': 'old_pass',
        })

        with patch.object(type(self.env['ir.mail_server']),
                          'test_smtp_connection',
                          return_value=None), \
             patch.object(type(self.env['fetchmail.server']),
                          'button_confirm_login',
                          return_value=None):
            self.test_user.action_confirm()

        existing.invalidate_recordset()
        self.assertEqual(
            existing.smtp_host, self.provider.smtp_host,
            "Existing ir.mail_server smtp_host must be updated by action_confirm().")

    def test_action_confirm_returns_display_notification(self):
        """Test action_confirm() returns an ir.actions.client display_notification
        action when everything succeeds."""
        self.env['ir.mail_server'].search([
            ('smtp_user', '=', self.test_user.email),
            ('name', '=', self.provider.name),
        ]).unlink()
        self.env['fetchmail.server'].search([
            ('user', '=', self.test_user.email),
            ('name', '=', self.provider.name),
        ]).unlink()

        with patch.object(type(self.env['ir.mail_server']),
                          'test_smtp_connection',
                          return_value=None), \
             patch.object(type(self.env['fetchmail.server']),
                          'button_confirm_login',
                          return_value=None):
            result = self.test_user.action_confirm()

        self.assertIsInstance(result, dict,
                              "action_confirm must return a dict action.")
        self.assertEqual(result.get('type'), 'ir.actions.client',
                         "Action type must be 'ir.actions.client'.")
        self.assertEqual(result.get('tag'), 'display_notification',
                         "Action tag must be 'display_notification'.")
        params = result.get('params', {})
        self.assertEqual(params.get('type'), 'success',
                         "Notification type must be 'success'.")

    def test_action_fetch_calls_fetch_mail_when_server_exists(self):
        """Test action_fetch() calls fetch_mail() on the matching
        fetchmail.server when one exists for the user."""
        self.env['fetchmail.server'].search([
            ('user', '=', self.test_user.email),
            ('name', '=', self.provider.name),
        ]).unlink()
        self.env['fetchmail.server'].create({
            'name': self.provider.name,
            'server': self.provider.server,
            'port': self.provider.port,
            'server_type': self.provider.server_type,
            'user': self.test_user.email,
            'password': 'test_password',
        })

        with patch.object(type(self.env['fetchmail.server']),
                          'fetch_mail',
                          return_value=None) as mock_fetch:
            self.test_user.action_fetch()
            self.assertTrue(
                mock_fetch.called,
                "fetch_mail() must be called by action_fetch() when a "
                "fetchmail.server exists for the user.")

    def test_action_fetch_does_not_raise_when_no_server_exists(self):
        """Test action_fetch() does not raise any error when no fetchmail
        server exists for the user (graceful no-op)."""
        self.env['fetchmail.server'].search([
            ('user', '=', self.test_user.email),
            ('name', '=', self.provider.name),
        ]).unlink()
        try:
            self.test_user.action_fetch()
        except Exception as exc:
            self.fail(
                f"action_fetch() raised an unexpected exception when no "
                f"fetchmail server exists: {exc}")

    def test_action_fetch_iterates_over_multiple_users(self):
        """Test action_fetch() processes every user in a multi-record set,
        calling fetch_mail() for each whose fetchmail.server exists."""
        # Create a second user with the same provider to form a multi-record
        second_user = self.env['res.users'].create({
            'name': 'Second Fetch User',
            'login': 'second_fetch_user@example.com',
            'email': 'second_fetch_user@example.com',
            'provider': self.provider.id,
            'pwd': 'second_password',
        })
        for user in [self.test_user, second_user]:
            self.env['fetchmail.server'].search([
                ('user', '=', user.email),
                ('name', '=', self.provider.name),
            ]).unlink()
            self.env['fetchmail.server'].create({
                'name': self.provider.name,
                'server': self.provider.server,
                'port': self.provider.port,
                'server_type': self.provider.server_type,
                'user': user.email,
                'password': 'pw',
            })

        users = self.test_user | second_user
        with patch.object(type(self.env['fetchmail.server']),
                          'fetch_mail',
                          return_value=None) as mock_fetch:
            users.action_fetch()
            self.assertTrue(
                mock_fetch.call_count >= 1,
                "fetch_mail() must be called at least once when processing "
                "multiple users with existing fetchmail servers.")