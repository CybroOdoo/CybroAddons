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

from unittest.mock import patch
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError


@tagged('post_install', '-at_install')
class TestResCompany(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.user.company_id

    def setUp(self):
        super().setUp()
        self.company.write({
            'hangout_client_id': False,
            'hangout_client_secret': False,
            'hangout_redirect_uri': False,
            'hangout_company_access_token': False,
            'hangout_company_access_token_expiry': False,
            'hangout_company_refresh_token': False,
            'hangout_company_authorization_code': False,
        })

    def test_01_action_google_meet_company_authenticate_validation(self):
        """Test authentication validation errors for missing configuration."""
        with self.assertRaises(ValidationError) as ctx:
            self.company.action_google_meet_company_authenticate()
        self.assertIn("Please enter the Client ID", str(ctx.exception))

        self.company.write({'hangout_client_id': 'test_client_id'})
        with self.assertRaises(ValidationError) as ctx:
            self.company.action_google_meet_company_authenticate()
        self.assertIn("Please enter the Authorized redirect URI", str(ctx.exception))

    def test_02_action_google_meet_company_authenticate_success(self):
        """Test successful URL action return for authentication."""
        self.company.write({
            'hangout_client_id': 'test_client_id',
            'hangout_redirect_uri': 'http://localhost:8069/google_meet_authentication',
        })
        res = self.company.action_google_meet_company_authenticate()
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        self.assertEqual(res.get('target'), 'new')
        self.assertIn('test_client_id', res.get('url'))
        self.assertIn('http://localhost:8069/google_meet_authentication', res.get('url'))
        # A fresh one-time state is stored and sent to Google
        state = self.company.hangout_oauth_state
        self.assertTrue(state)
        self.assertIn('&state=%s' % state, res.get('url'))
        self.company.action_google_meet_company_authenticate()
        self.assertNotEqual(self.company.hangout_oauth_state, state)

    def test_03_action_google_meet_company_refresh_token_validation(self):
        """Test validation for refresh token configuration."""
        with self.assertRaises(UserError) as ctx:
            self.company.action_google_meet_company_refresh_token()
        self.assertIn("Client ID is not yet configured", str(ctx.exception))

        self.company.write({'hangout_client_id': 'test_client_id'})
        with self.assertRaises(UserError) as ctx:
            self.company.action_google_meet_company_refresh_token()
        self.assertIn("Client Secret is not yet configured", str(ctx.exception))

        self.company.write({
            'hangout_client_id': 'test_client_id',
            'hangout_client_secret': 'test_client_secret',
        })
        with self.assertRaises(UserError) as ctx:
            self.company.action_google_meet_company_refresh_token()
        self.assertIn("Refresh Token is not yet configured", str(ctx.exception))

    def test_04_action_google_meet_company_refresh_token_success(self):
        """Test successful token refresh updates access token."""
        self.company.write({
            'hangout_client_id': 'test_client_id',
            'hangout_client_secret': 'test_client_secret',
            'hangout_company_refresh_token': 'test_refresh_token',
        })

        mock_response = {
            'access_token': 'new_access_token_xyz',
            'expires_in': 3600,
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.status_code = 200

            self.company.action_google_meet_company_refresh_token()
            self.assertEqual(self.company.hangout_company_access_token, 'new_access_token_xyz')
            self.assertTrue(self.company.hangout_company_access_token_expiry)

    def test_05_action_google_meet_company_refresh_token_failure(self):
        """Test token refresh failure raises UserError."""
        self.company.write({
            'hangout_client_id': 'test_client_id',
            'hangout_client_secret': 'test_client_secret',
            'hangout_company_refresh_token': 'test_refresh_token',
        })

        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {'error': 'invalid_grant'}
            mock_post.return_value.status_code = 400

            with self.assertRaises(UserError) as ctx:
                self.company.action_google_meet_company_refresh_token()
            self.assertIn("Something went wrong during the token generation", str(ctx.exception))

    def test_06_google_meet_company_refresh_token_helper(self):
        """Test the helper delegates to the refresh token action."""
        self.company.write({
            'hangout_client_id': 'test_client_id',
            'hangout_client_secret': 'test_client_secret',
            'hangout_company_refresh_token': 'test_refresh_token',
        })
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                'access_token': 'helper_access_token'}
            self.company.google_meet_company_refresh_token()
            self.assertEqual(self.company.hangout_company_access_token,
                             'helper_access_token')
