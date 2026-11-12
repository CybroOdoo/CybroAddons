# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith CK (odoo@cybrosys.com)
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
from urllib.parse import parse_qs, urlparse
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, new_test_user, tagged
from .common import create_account, mock_response

REQUESTS_PATH = ('odoo.addons.google_drive_odoo_connector.models.'
                 'google_drive_account.requests')


@tagged('post_install', '-at_install')
class TestGoogleDriveAccount(TransactionCase):
    """Test cases for google.drive.account defined in
    google_drive_odoo_connector/models/google_drive_account.py"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account = create_account(cls.env)
        cls.ICP = cls.env['ir.config_parameter'].sudo()

    def _auth_params(self, action):
        """Return the query parameters of the OAuth URL in an action."""
        return {key: value[0] for key, value in
                parse_qs(urlparse(action['url']).query).items()}

    # ------------------------------------------------------------------
    # action_connect
    # ------------------------------------------------------------------
    def test_action_connect_uses_configured_redirect_uri(self):
        """A configured google_drive.redirect_uri is used as-is."""
        self.ICP.set_param('google_drive.redirect_uri',
                           'https://example.com/cb')
        action = self.account.action_connect()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['target'], 'self')
        self.assertTrue(action['url'].startswith(
            'https://accounts.google.com/o/oauth2/v2/auth?'))
        params = self._auth_params(action)
        self.assertEqual(params['redirect_uri'], 'https://example.com/cb')
        self.assertEqual(params['client_id'], 'client-id')
        self.assertEqual(params['state'], self.account._get_oauth_state())
        self.assertTrue(params['state'].startswith('%s:' % self.account.id))
        self.assertEqual(params['access_type'], 'offline')
        self.assertEqual(params['scope'],
                         'https://www.googleapis.com/auth/drive')

    def test_action_connect_https_base_url(self):
        """Without a configured redirect URI, an https base URL is kept."""
        self.ICP.set_param('google_drive.redirect_uri', False)
        self.ICP.set_param('web.base.url', 'https://odoo.example.com')
        params = self._auth_params(self.account.action_connect())
        self.assertEqual(
            params['redirect_uri'],
            'https://odoo.example.com/google_drive/oauth/callback')

    def test_action_connect_http_base_url_rewritten_to_localhost(self):
        """A plain http, non-local base URL is rewritten to localhost."""
        self.ICP.set_param('google_drive.redirect_uri', False)
        self.ICP.set_param('web.base.url', 'http://192.168.1.10:8069')
        params = self._auth_params(self.account.action_connect())
        self.assertEqual(params['redirect_uri'],
                         'http://localhost:8069/google_drive/oauth/callback')

    def test_get_account_from_oauth_state(self):
        """Only a correctly signed state resolves to the account."""
        Account = self.env['google.drive.account']
        self.assertEqual(Account._get_account_from_oauth_state(
            self.account._get_oauth_state()), self.account)
        for state in (False, '', str(self.account.id),
                      '%s:forged' % self.account.id, 'abc:def'):
            self.assertFalse(Account._get_account_from_oauth_state(state))

    def test_get_connected_account(self):
        """The connected account is found even without access rights."""
        user = new_test_user(self.env, login='gdrive_no_access',
                             groups='base.group_portal')
        Account = self.env['google.drive.account'].with_user(user)
        self.assertTrue(Account._get_connected_account())

    # ------------------------------------------------------------------
    # exchange_authorization_code
    # ------------------------------------------------------------------
    def test_exchange_authorization_code_success(self):
        """A valid code stores the tokens and marks the account connected."""
        account = create_account(self.env, state='draft', access_token=False,
                                 refresh_token=False, token_expiry=False)
        self.ICP.set_param('google_drive.redirect_uri',
                           'https://example.com/cb')
        response = mock_response(json_data={
            'access_token': 'new-access',
            'refresh_token': 'new-refresh',
            'expires_in': 3600,
        })
        with patch(REQUESTS_PATH + '.post', return_value=response) as post:
            account.exchange_authorization_code('auth-code')
        payload = post.call_args.kwargs['data']
        self.assertEqual(payload['code'], 'auth-code')
        self.assertEqual(payload['grant_type'], 'authorization_code')
        self.assertEqual(payload['redirect_uri'], 'https://example.com/cb')
        self.assertEqual(account.state, 'connected')
        self.assertEqual(account.access_token, 'new-access')
        self.assertEqual(account.refresh_token, 'new-refresh')
        self.assertGreater(account.token_expiry, fields.Datetime.now())

    def test_exchange_authorization_code_failure(self):
        """A failed token exchange raises a UserError."""
        response = mock_response(status_code=400, text='invalid_request')
        with patch(REQUESTS_PATH + '.post', return_value=response), \
                self.assertRaises(UserError):
            self.account.exchange_authorization_code('bad-code')

    # ------------------------------------------------------------------
    # _refresh_access_token
    # ------------------------------------------------------------------
    def test_refresh_access_token_without_refresh_token(self):
        """Refreshing without a refresh token raises a UserError."""
        self.account.refresh_token = False
        with patch(REQUESTS_PATH + '.post') as post, \
                self.assertRaises(UserError):
            self.account._refresh_access_token()
        post.assert_not_called()

    def test_refresh_access_token_success(self):
        """A successful refresh stores the new token and expiry."""
        response = mock_response(json_data={
            'access_token': 'refreshed-token', 'expires_in': 3600})
        with patch(REQUESTS_PATH + '.post', return_value=response) as post:
            self.account._refresh_access_token()
        self.assertEqual(post.call_args.kwargs['data']['grant_type'],
                         'refresh_token')
        self.assertEqual(self.account.access_token, 'refreshed-token')
        self.assertGreater(self.account.token_expiry, fields.Datetime.now())

    def test_refresh_access_token_invalid_grant(self):
        """An invalid_grant error asks the user to reconnect the account."""
        response = mock_response(status_code=400,
                                 json_data={'error': 'invalid_grant'})
        with patch(REQUESTS_PATH + '.post', return_value=response), \
                self.assertRaisesRegex(UserError, 'reconnect'):
            self.account._refresh_access_token()

    def test_refresh_access_token_other_error(self):
        """Any other error raises a UserError without touching the state."""
        response = mock_response(status_code=500,
                                 json_data={'error': 'backend_error'},
                                 text='backend_error')
        with patch(REQUESTS_PATH + '.post', return_value=response), \
                self.assertRaises(UserError):
            self.account._refresh_access_token()
        self.assertEqual(self.account.state, 'connected')

    # ------------------------------------------------------------------
    # _get_headers
    # ------------------------------------------------------------------
    def test_get_headers_valid_token(self):
        """A valid token is used without contacting Google."""
        with patch(REQUESTS_PATH + '.post') as post:
            headers = self.account._get_headers()
        post.assert_not_called()
        self.assertEqual(headers, {'Authorization': 'Bearer access-token'})

    def test_get_headers_expired_token_is_refreshed(self):
        """An expired token is refreshed before building the headers."""
        self.account.token_expiry = fields.Datetime.now() - timedelta(hours=1)
        response = mock_response(json_data={
            'access_token': 'refreshed-token', 'expires_in': 3600})
        with patch(REQUESTS_PATH + '.post', return_value=response) as post:
            headers = self.account._get_headers()
        post.assert_called_once()
        self.assertEqual(headers,
                         {'Authorization': 'Bearer refreshed-token'})

    def test_get_headers_missing_token_is_refreshed(self):
        """A missing access token triggers a refresh."""
        self.account.access_token = False
        response = mock_response(json_data={
            'access_token': 'refreshed-token', 'expires_in': 3600})
        with patch(REQUESTS_PATH + '.post', return_value=response) as post:
            headers = self.account._get_headers()
        post.assert_called_once()
        self.assertEqual(headers['Authorization'], 'Bearer refreshed-token')

    # ------------------------------------------------------------------
    # action_test_connection / download_file
    # ------------------------------------------------------------------
    def test_action_test_connection_success(self):
        """A successful API call returns a success notification."""
        response = mock_response(json_data={'files': []})
        with patch(REQUESTS_PATH + '.get', return_value=response) as get:
            action = self.account.action_test_connection()
        self.assertEqual(get.call_args.kwargs['headers'],
                         {'Authorization': 'Bearer access-token'})
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'success')

    def test_action_test_connection_failure(self):
        """An HTTP error from the API is propagated."""
        response = mock_response(status_code=401)
        with patch(REQUESTS_PATH + '.get', return_value=response), \
                self.assertRaises(Exception):
            self.account.action_test_connection()

    def test_download_file(self):
        """download_file returns the raw content of the Drive file."""
        response = mock_response(content=b'file content')
        with patch(REQUESTS_PATH + '.get', return_value=response) as get:
            content = self.account.download_file('gfile_123')
        self.assertEqual(content, b'file content')
        self.assertIn('/files/gfile_123?alt=media', get.call_args.args[0])
