# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResUsersGoogleCalendar(TransactionCase):
    """Test Google Calendar fields and actions on res.users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.user

    def _set_google_calendar_config(self):
        """Configure Google Calendar OAuth parameters for the tests."""
        config = self.env['ir.config_parameter'].sudo()
        config.set_param('google_calendar_client_id', 'client_id')
        config.set_param('google_calendar_client_secret', 'client_secret')

    def _clear_google_calendar_config(self):
        """Remove Google Calendar OAuth parameters for negative tests."""
        self.env['ir.config_parameter'].sudo().search([
            ('key', 'in', [
                'google_calendar_client_id',
                'google_calendar_client_secret',
            ]),
        ]).unlink()

    def test_is_valid_email(self):
        """Email validation accepts valid addresses and rejects invalid ones."""
        self.user.google_user_mail = 'calendar.user@example.com'
        self.assertTrue(self.user.is_valid_email())

        self.user.google_user_mail = 'calendar-user'
        self.assertFalse(self.user.is_valid_email())

    def test_set_auth_tokens_updates_user_token_fields(self):
        """Authentication tokens are stored with a computed validity date."""
        before_update = fields.Datetime.now()

        self.user._set_auth_tokens('access_token', 'refresh_token', 3600)

        self.assertEqual(self.user.user_token, 'access_token')
        self.assertEqual(self.user.refresh_token, 'refresh_token')
        self.assertGreaterEqual(self.user.last_sync_date, before_update)

    def test_authenticate_button_requires_google_config(self):
        """Authentication fails when OAuth client settings are missing."""
        self._clear_google_calendar_config()

        with self.assertRaises(UserError):
            self.user.authenticate_button()

    def test_authenticate_button_validates_api_key_and_email(self):
        """Authentication rejects an invalid API key or calendar email."""
        self._set_google_calendar_config()
        self.user.write({
            'api_key': 'short',
            'google_user_mail': 'invalid-email',
        })

        with self.assertRaises(UserError):
            self.user.authenticate_button()

    def test_authenticate_button_requires_google_calendar_token(self):
        """Authentication rejects users without a Google Calendar token."""
        self._set_google_calendar_config()
        self.user.write({
            'api_key': 'valid_google_api_key',
            'google_user_mail': 'calendar.user@example.com',
            'google_calendar_rtoken': False,
        })

        with self.assertRaises(UserError):
            self.user.authenticate_button()

    def test_authenticate_button_stores_google_calendar_tokens(self):
        """Successful authentication stores tokens from google_calendar fields."""
        self._set_google_calendar_config()
        validity = fields.Datetime.now() + timedelta(hours=1)
        self.user.write({
            'api_key': 'valid_google_api_key',
            'google_user_mail': 'calendar.user@example.com',
            'google_calendar_rtoken': 'calendar_refresh_token',
            'google_calendar_token': 'calendar_user_token',
            'google_calendar_token_validity': validity,
        })

        action = self.user.authenticate_button()

        self.assertEqual(self.user.refresh_token, 'calendar_refresh_token')
        self.assertEqual(self.user.user_token, 'calendar_user_token')
        self.assertEqual(self.user.last_sync_date, validity)
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'success')

    def test_refresh_button_requires_google_config(self):
        """Refreshing tokens fails when OAuth client settings are missing."""
        self._clear_google_calendar_config()

        with self.assertRaises(UserError):
            self.user.refresh_button()

    def test_refresh_button_requires_refresh_token(self):
        """Refreshing tokens fails before calling Google when token is missing."""
        self._set_google_calendar_config()
        self.user.write({
            'refresh_token': False,
            'google_calendar_rtoken': False,
        })

        with self.assertRaises(UserError):
            self.user.refresh_button()

    def test_refresh_button_updates_access_token(self):
        """Refresh uses Google service and stores the returned access token."""
        self._set_google_calendar_config()
        self.user.refresh_token = 'existing_refresh_token'

        with patch.object(
                type(self.env['google.service']),
                '_refresh_google_token',
                return_value=('new_access_token', 3600)) as mock_refresh:
            self.user.refresh_button()

        mock_refresh.assert_called_once_with('calendar', 'existing_refresh_token')
        self.assertEqual(self.user.user_token, 'new_access_token')
        self.assertTrue(self.user.last_sync_date)
