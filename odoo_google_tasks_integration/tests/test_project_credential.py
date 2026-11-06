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
from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import POST, GoogleTasksCommon, mock_response


@tagged('post_install', '-at_install')
class TestProjectCredential(GoogleTasksCommon):

    def test_default_redirect_uri(self):
        base_url = self.env['ir.config_parameter'].get_str('web.base.url')
        self.assertEqual(self.env['project.credential'].new({})
                         .hangout_redirect_uri,
                         base_url + '/google_task_authentication')

    def test_authenticate_url(self):
        self.credential.hangout_redirect_uri = \
            'https://odoo.example.com/google_task_authentication'
        action = self.credential.action_google_task_company_authenticate()
        query = parse_qs(urlparse(action['url']).query)
        self.assertEqual(query['client_id'], ['client-id'])
        self.assertEqual(query['scope'],
                         ['https://www.googleapis.com/auth/tasks'])
        self.assertEqual(query['redirect_uri'],
                         ['https://odoo.example.com/google_task_authentication'])
        self.assertEqual(query['access_type'], ['offline'])
        self.assertEqual(query['prompt'], ['consent'])
        self.assertEqual(query['state'],
                         [self.credential._get_oauth_state()])

    def test_authenticate_requires_client(self):
        self.credential.hangout_client_secret = False
        with self.assertRaises(UserError):
            self.credential.action_google_task_company_authenticate()

    @patch(POST)
    def test_exchange_code_stores_refresh_token(self, mock_post):
        mock_post.return_value = mock_response(json={
            'access_token': 'new-access', 'refresh_token': 'new-refresh',
            'expires_in': 3599})
        self.credential._exchange_authorization_code('auth-code')
        self.assertEqual(mock_post.call_args.kwargs['data']['code'],
                         'auth-code')
        self.assertEqual(self.credential.hangout_company_access_token,
                         'new-access')
        self.assertEqual(self.credential.hangout_company_refresh_token,
                         'new-refresh')
        self.assertEqual(self.credential.hangout_company_authorization_code,
                         'auth-code')

    @patch(POST)
    def test_refresh_keeps_refresh_token(self, mock_post):
        mock_post.return_value = mock_response(json={
            'access_token': 'refreshed', 'expires_in': 3599})
        action = self.credential.action_google_task_company_refresh_token()
        self.assertEqual(action['params']['type'], 'success')
        self.assertEqual(mock_post.call_args.kwargs['data']['grant_type'],
                         'refresh_token')
        self.assertEqual(self.credential.hangout_company_access_token,
                         'refreshed')
        self.assertEqual(self.credential.hangout_company_refresh_token,
                         'refresh-token')

    @patch(POST)
    def test_token_error(self, mock_post):
        mock_post.return_value = mock_response(
            400, json={'error': 'invalid_grant'})
        with self.assertRaises(UserError):
            self.credential._refresh_access_token()

    @patch(POST)
    def test_expired_token_is_refreshed(self, mock_post):
        mock_post.return_value = mock_response(json={
            'access_token': 'refreshed', 'expires_in': 3599})
        self.credential.hangout_company_access_token_expiry = \
            fields.Datetime.now() - timedelta(minutes=5)
        self.assertEqual(self.credential._get_access_token(), 'refreshed')
        mock_post.reset_mock()
        self.assertEqual(self.credential._get_access_token(), 'refreshed')
        mock_post.assert_not_called()
