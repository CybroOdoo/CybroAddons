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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Unit tests for GitHub OAuth Login module."""

import json
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from werkzeug.exceptions import BadRequest

from odoo.exceptions import AccessDenied
from odoo.http import Response
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.github_login_odoo.controllers.github_login_odoo import (
    GitHubOAuthLogin,
    GitHubOAuthController,
    CallbackHandler,
)


@tagged('post_install', '-at_install')
class TestGitHubOAuthProvider(TransactionCase):
    """Tests for auth.oauth.provider model enhancements."""

    def test_compute_is_github(self):
        """Test is_github compute field based on auth_endpoint or validation_endpoint."""
        provider_github = self.env['auth.oauth.provider'].create({
            'name': 'Corporate Git Login',  # Name does not have 'github'
            'body': 'Log in with GitHub',
            'auth_endpoint': 'https://github.com/login/oauth/authorize',
            'validation_endpoint': 'https://github.com/login/oauth/access_token',
        })
        self.assertTrue(provider_github.is_github)
        self.assertIsInstance(provider_github.is_github, bool)

        provider_other = self.env['auth.oauth.provider'].create({
            'name': 'Google Test',
            'body': 'Log in with Google',
            'auth_endpoint': 'https://accounts.google.com/o/oauth2/auth',
            'validation_endpoint': 'https://www.googleapis.com/oauth2/v1/tokeninfo',
        })
        self.assertFalse(provider_other.is_github)
        self.assertIsInstance(provider_other.is_github, bool)

        provider_other.write({'auth_endpoint': 'https://example.com/oauth'})
        self.assertFalse(provider_other.is_github)
        self.assertIsInstance(provider_other.is_github, bool)

        # Endpoint with github in validation_endpoint
        provider_custom = self.env['auth.oauth.provider'].create({
            'name': 'Enterprise SSO',
            'body': 'Log in with SSO',
            'auth_endpoint': 'https://oauth.mycompany.com/authorize',
            'validation_endpoint': 'https://api.github.com/user',
        })
        self.assertTrue(provider_custom.is_github)

    def test_client_secret_field(self):
        """Test that client_secret field can be written and read."""
        provider = self.env['auth.oauth.provider'].create({
            'name': 'GitHub Secret Test',
            'body': 'Log in with GitHub',
            'auth_endpoint': 'https://github.com/login/oauth/authorize',
            'validation_endpoint': 'https://github.com/login/oauth/access_token',
            'client_secret': 'super_secret_key_123',
        })
        self.assertEqual(provider.client_secret, 'super_secret_key_123')

    def test_default_github_provider_data(self):
        """Test default GitHub provider XML record."""
        provider = self.env.ref('github_login_odoo.auth_oauth_provider_github', raise_if_not_found=False)
        if provider:
            self.assertEqual(provider.name, 'GitHub')
            self.assertEqual(provider.body, 'Log in with GitHub')
            self.assertTrue(provider.is_github)


@tagged('post_install', '-at_install')
class TestGitHubResUsers(TransactionCase):
    """Tests for res.users OAuth methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env['auth.oauth.provider'].create({
            'name': 'GitHub Provider',
            'body': 'Log in with GitHub',
            'client_id': 'test_client_id_123',
            'client_secret': 'test_client_secret_456',
            'auth_endpoint': 'https://github.com/login/oauth/authorize',
            'validation_endpoint': 'https://github.com/login/oauth/access_token',
        })
        cls.google_provider = cls.env['auth.oauth.provider'].create({
            'name': 'Google Provider',
            'body': 'Log in with Google',
            'client_id': 'google_client_id',
            'auth_endpoint': 'https://accounts.google.com/o/oauth2/auth',
            'validation_endpoint': 'https://www.googleapis.com/oauth2/v1/tokeninfo',
        })

    @patch('requests.get')
    @patch('requests.post')
    def test_auth_oauth_rpc_github_success(self, mock_post, mock_get):
        """Test successful GitHub token exchange and profile retrieval."""
        mock_token_resp = MagicMock()
        mock_token_resp.ok = True
        mock_token_resp.json.return_value = {'access_token': 'gho_real_token_xyz'}
        mock_post.return_value = mock_token_resp

        mock_emails_resp = MagicMock()
        mock_emails_resp.ok = True
        mock_emails_resp.json.return_value = [
            {'email': 'secondary@example.com', 'primary': False},
            {'email': 'primary@example.com', 'primary': True},
        ]

        mock_user_resp = MagicMock()
        mock_user_resp.ok = True
        mock_user_resp.json.return_value = {
            'id': 1234567,
            'login': 'octocat',
            'name': 'The Octocat',
        }

        mock_get.side_effect = [mock_emails_resp, mock_user_resp]

        res_users = self.env['res.users'].with_context(github=True, provider=self.provider.id)
        result = res_users._auth_oauth_rpc(self.provider.validation_endpoint, 'dummy_auth_code')

        self.assertEqual(result.get('key'), 'gho_real_token_xyz')
        self.assertEqual(result.get('user_id'), 1234567)
        self.assertEqual(result.get('username'), 'octocat')
        self.assertEqual(result.get('name'), 'The Octocat')
        self.assertEqual(result.get('email'), 'primary@example.com')

    @patch('requests.get')
    @patch('requests.post')
    def test_auth_oauth_rpc_github_fallback_email(self, mock_post, mock_get):
        """Test fallback email when no email is marked primary."""
        mock_token_resp = MagicMock()
        mock_token_resp.ok = True
        mock_token_resp.json.return_value = {'access_token': 'gho_token'}
        mock_post.return_value = mock_token_resp

        mock_emails_resp = MagicMock()
        mock_emails_resp.ok = True
        mock_emails_resp.json.return_value = [
            {'email': 'fallback@example.com', 'primary': False},
        ]

        mock_user_resp = MagicMock()
        mock_user_resp.ok = True
        mock_user_resp.json.return_value = {
            'id': 8888,
            'login': 'user8888',
        }

        mock_get.side_effect = [mock_emails_resp, mock_user_resp]

        res_users = self.env['res.users'].with_context(github=True, provider=self.provider.id)
        result = res_users._auth_oauth_rpc(self.provider.validation_endpoint, 'dummy_auth_code')

        self.assertEqual(result.get('email'), 'fallback@example.com')
        self.assertEqual(result.get('name'), 'user8888')

    @patch('requests.post')
    def test_auth_oauth_rpc_token_exchange_failed(self, mock_post):
        """Test handling of failed token exchange response."""
        mock_token_resp = MagicMock()
        mock_token_resp.ok = False
        mock_token_resp.status_code = 400
        mock_token_resp.text = 'Bad Request'
        mock_post.return_value = mock_token_resp

        res_users = self.env['res.users'].with_context(github=True, provider=self.provider.id)
        result = res_users._auth_oauth_rpc(self.provider.validation_endpoint, 'bad_code')
        self.assertEqual(result, {'error': 'token_exchange_failed'})

    @patch('requests.post')
    def test_auth_oauth_rpc_github_api_error(self, mock_post):
        """Test handling when GitHub returns an error in JSON body."""
        mock_token_resp = MagicMock()
        mock_token_resp.ok = True
        mock_token_resp.json.return_value = {
            'error': 'bad_verification_code',
            'error_description': 'The code passed is incorrect or expired.',
        }
        mock_post.return_value = mock_token_resp

        res_users = self.env['res.users'].with_context(github=True, provider=self.provider.id)
        result = res_users._auth_oauth_rpc(self.provider.validation_endpoint, 'expired_code')
        self.assertEqual(result, {'error': 'bad_verification_code'})

    @patch('requests.get')
    @patch('requests.post')
    def test_auth_oauth_rpc_email_fetch_failed(self, mock_post, mock_get):
        """Test error when user email fetch fails."""
        mock_token_resp = MagicMock()
        mock_token_resp.ok = True
        mock_token_resp.json.return_value = {'access_token': 'gho_token'}
        mock_post.return_value = mock_token_resp

        mock_emails_resp = MagicMock()
        mock_emails_resp.ok = False
        mock_emails_resp.text = 'Unauthorized'
        mock_get.return_value = mock_emails_resp

        res_users = self.env['res.users'].with_context(github=True, provider=self.provider.id)
        result = res_users._auth_oauth_rpc(self.provider.validation_endpoint, 'code')
        self.assertEqual(result, {'error': 'email_fetch_failed'})

    @patch('requests.get')
    @patch('requests.post')
    def test_auth_oauth_rpc_profile_fetch_failed(self, mock_post, mock_get):
        """Test error when user profile fetch fails."""
        mock_token_resp = MagicMock()
        mock_token_resp.ok = True
        mock_token_resp.json.return_value = {'access_token': 'gho_token'}
        mock_post.return_value = mock_token_resp

        mock_emails_resp = MagicMock()
        mock_emails_resp.ok = True
        mock_emails_resp.json.return_value = [{'email': 'a@b.com', 'primary': True}]

        mock_user_resp = MagicMock()
        mock_user_resp.ok = False
        mock_user_resp.text = 'Rate Limited'

        mock_get.side_effect = [mock_emails_resp, mock_user_resp]

        res_users = self.env['res.users'].with_context(github=True, provider=self.provider.id)
        result = res_users._auth_oauth_rpc(self.provider.validation_endpoint, 'code')
        self.assertEqual(result, {'error': 'profile_fetch_failed'})

    def test_auth_oauth_rpc_non_github_context_delegates(self):
        """Test that _auth_oauth_rpc delegates to super when github context is absent."""
        with patch('odoo.addons.auth_oauth.models.res_users.ResUsers._auth_oauth_rpc', return_value={'user_id': 'g123'}) as mock_super_rpc:
            res_users = self.env['res.users']  # No github context
            res = res_users._auth_oauth_rpc('https://googleapis.com/oauth2', 'token123')
            mock_super_rpc.assert_called_once_with('https://googleapis.com/oauth2', 'token123')
            self.assertEqual(res, {'user_id': 'g123'})

    def test_auth_oauth_validate_github_error_raises_access_denied(self):
        """Test that _auth_oauth_validate raises AccessDenied when RPC returns error."""
        with patch.object(
            type(self.env['res.users']),
            '_auth_oauth_rpc',
            return_value={'error': 'bad_verification_code'}
        ):
            res_users = self.env['res.users'].with_context(github=True)
            with self.assertRaises(AccessDenied):
                res_users._auth_oauth_validate(self.provider.id, 'bad_token')

    def test_auth_oauth_validate_github_success(self):
        """Test that _auth_oauth_validate returns validation dictionary on success."""
        valid_data = {
            'key': 'real_token',
            'user_id': 999,
            'username': 'testuser',
            'email': 'testuser@example.com',
        }
        with patch.object(type(self.env['res.users']), '_auth_oauth_rpc', return_value=valid_data):
            res_users = self.env['res.users'].with_context(github=True)
            validation = res_users._auth_oauth_validate(self.provider.id, 'auth_code')
            self.assertEqual(validation.get('user_id'), 999)
            self.assertEqual(validation.get('key'), 'real_token')

    def test_auth_oauth_github_flow(self):
        """Test the full auth_oauth method override for GitHub provider."""
        validation_data = {
            'key': 'gho_real_secret_token',
            'user_id': 12345,
            'email': 'user@example.com',
        }
        with patch.object(type(self.env['res.users']), '_auth_oauth_validate', return_value=validation_data), \
             patch.object(type(self.env['res.users']), '_auth_oauth_signin', return_value='user@example.com'):
            params = {'access_token': 'temp_code'}
            res_users = self.env['res.users']
            dbname, login, token = res_users.auth_oauth(self.provider.id, params)

            self.assertEqual(dbname, self.env.cr.dbname)
            self.assertEqual(login, 'user@example.com')
            self.assertEqual(token, 'gho_real_secret_token')
            self.assertEqual(params['access_token'], 'gho_real_secret_token')

    def test_auth_oauth_github_signin_denied(self):
        """Test that auth_oauth raises AccessDenied if _auth_oauth_signin fails."""
        validation_data = {'key': 'token', 'user_id': 1}
        with patch.object(type(self.env['res.users']), '_auth_oauth_validate', return_value=validation_data), \
             patch.object(type(self.env['res.users']), '_auth_oauth_signin', return_value=False):
            params = {'access_token': 'temp_code'}
            res_users = self.env['res.users']
            with self.assertRaises(AccessDenied):
                res_users.auth_oauth(self.provider.id, params)

    def test_auth_oauth_non_github_provider_delegates_to_super(self):
        """Test that auth_oauth with a non-GitHub provider calls standard core auth_oauth."""
        expected_result = (self.env.cr.dbname, 'google_user@example.com', 'google_access_token')
        with patch('odoo.addons.auth_oauth.models.res_users.ResUsers.auth_oauth', return_value=expected_result) as mock_super_auth:
            params = {'access_token': 'google_access_token'}
            res_users = self.env['res.users']
            result = res_users.auth_oauth(self.google_provider.id, params)
            mock_super_auth.assert_called_once_with(self.google_provider.id, params)
            self.assertEqual(result, expected_result)


@tagged('post_install', '-at_install')
class TestGitHubLoginControllers(TransactionCase):
    """Tests for GitHub OAuth controller functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env['auth.oauth.provider'].create({
            'name': 'Custom GitHub Gateway',
            'body': 'Log in with GitHub',
            'client_id': 'gh_cid_123',
            'client_secret': 'gh_sec_456',
            'scope': 'user:email',
            'auth_endpoint': 'https://github.com/login/oauth/authorize',
            'validation_endpoint': 'https://github.com/login/oauth/access_token',
        })
        cls.google_provider = cls.env['auth.oauth.provider'].create({
            'name': 'Google Workspace',
            'body': 'Log in with Google',
            'client_id': 'google_cid_789',
            'scope': 'openid email profile',
            'auth_endpoint': 'https://accounts.google.com/o/oauth2/auth',
            'validation_endpoint': 'https://www.googleapis.com/oauth2/v1/tokeninfo',
        })

    def test_list_providers_auth_link_by_endpoint(self):
        """Test list_providers detects GitHub by endpoint/is_github even if name differs."""
        controller = GitHubOAuthLogin()
        mock_provider_gh = {
            'id': self.provider.id,
            'name': 'Company Single Sign-On',  # Name does not mention GitHub
            'is_github': True,
            'client_id': 'gh_client_123',
            'scope': 'user:email',
            'auth_endpoint': 'https://github.com/login/oauth/authorize',
        }
        mock_provider_google = {
            'id': self.google_provider.id,
            'name': 'Google Auth',
            'is_github': False,
            'client_id': 'google_client_123',
            'scope': 'email',
            'auth_endpoint': 'https://accounts.google.com/o/oauth2/auth',
            'auth_link': 'https://accounts.google.com/o/oauth2/auth?original=1',
        }
        with patch.object(GitHubOAuthLogin, 'get_state', return_value={'d': 'test_db', 'p': self.provider.id}), \
             patch('odoo.addons.auth_oauth.controllers.main.OAuthLogin.list_providers', return_value=[mock_provider_gh, mock_provider_google]):
            providers = controller.list_providers()
            self.assertEqual(len(providers), 2)

            # GitHub provider updated
            auth_link = providers[0].get('auth_link')
            self.assertTrue(auth_link.startswith('https://github.com/login/oauth/authorize?'))
            parsed = urlparse(auth_link)
            qs = parse_qs(parsed.query)
            self.assertEqual(qs.get('client_id'), ['gh_client_123'])
            self.assertEqual(qs.get('scope'), ['user:email'])
            self.assertIn('state', qs)

            # Google provider unchanged
            self.assertEqual(providers[1].get('auth_link'), 'https://accounts.google.com/o/oauth2/auth?original=1')

    def test_web_login_error_messages(self):
        """Test web_login maps custom GitHub error codes without overwriting standard error 3."""
        import odoo.http
        controller = GitHubOAuthLogin()
        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.httprequest.method = 'GET'
        mock_req.session.uid = False
        mock_req.params = {'oauth_error': '4'}

        mock_response = Response(template='web.login', qcontext={})

        token = odoo.http.request_var.set(mock_req)
        try:
            with patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.request', mock_req), \
                 patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.ensure_db'), \
                 patch.object(GitHubOAuthLogin, 'list_providers', return_value=[]), \
                 patch('odoo.addons.auth_oauth.controllers.main.OAuthLogin.web_login', return_value=mock_response):

                res = controller.web_login()
                self.assertIn("Validation endpoint is missing", res.qcontext.get('error', ''))

                # Test error 6
                mock_req.params = {'oauth_error': '6'}
                res = controller.web_login()
                self.assertIn("Client ID or Client Secret is not present", res.qcontext.get('error', ''))

                # Test that oauth_error=3 does NOT map to "Email already exists"
                mock_req.params = {'oauth_error': '3'}
                mock_response.qcontext = {'error': 'Standard invitation expired message'}
                res = controller.web_login()
                self.assertNotEqual(res.qcontext.get('error'), "Email already exists.\nPlease contact your administrator.")
                self.assertEqual(res.qcontext.get('error'), 'Standard invitation expired message')
        finally:
            odoo.http.request_var.reset(token)

    def test_signin_github_provider_sets_context(self):
        """Test that signin sets github=True in state context for GitHub provider."""
        controller = GitHubOAuthController()
        state = {'d': self.env.cr.dbname, 'p': self.provider.id, 'c': {}}
        kw = {'state': json.dumps(state), 'access_token': 'dummy_code'}

        mock_req = MagicMock()
        mock_req.env = self.env

        with patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.request', mock_req), \
             patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.db_filter', return_value=True), \
             patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.ensure_db'), \
             patch('odoo.addons.auth_oauth.controllers.main.OAuthController.signin', return_value=Response('ok')) as mock_super_signin:

            controller.signin(**kw)
            mock_super_signin.assert_called_once()
            called_kw = mock_super_signin.call_args[1]
            called_state = json.loads(called_kw['state'])
            self.assertTrue(called_state.get('c', {}).get('github'))
            self.assertEqual(called_state.get('c', {}).get('provider'), self.provider.id)

    def test_signin_non_github_provider_preserves_flow(self):
        """Test that signin for non-GitHub provider (e.g. Google) does NOT set github=True."""
        controller = GitHubOAuthController()
        state = {'d': self.env.cr.dbname, 'p': self.google_provider.id, 'c': {}}
        kw = {'state': json.dumps(state), 'access_token': 'google_token'}

        mock_req = MagicMock()
        mock_req.env = self.env

        with patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.request', mock_req), \
             patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.db_filter', return_value=True), \
             patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.ensure_db'), \
             patch('odoo.addons.auth_oauth.controllers.main.OAuthController.signin', return_value=Response('ok')) as mock_super_signin:

            controller.signin(**kw)
            mock_super_signin.assert_called_once()
            called_kw = mock_super_signin.call_args[1]
            called_state = json.loads(called_kw['state'])
            # Verify github context is NOT set for Google provider
            self.assertNotIn('github', called_state.get('c', {}))
            self.assertNotIn('provider', called_state.get('c', {}))

    def test_signin_invalid_state(self):
        """Test that signin raises BadRequest when state parameter is malformed."""
        controller = GitHubOAuthController()
        kw = {'state': 'not-json-valid'}
        with self.assertRaises(BadRequest):
            controller.signin(**kw)

    def test_callback_handler_with_code_success(self):
        """Test callback redirection when code is present."""
        handler = CallbackHandler()
        mock_request = MagicMock()
        mock_request.httprequest.url_root = 'https://odoo.example.com/'
        mock_request.env = self.env
        mock_request.redirect.side_effect = lambda url, code=302: Response('redirect', status=code)

        with patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.request', mock_request):
            state_data = json.dumps({'p': self.provider.id})
            handler.get_oauth_token(code='oauth_code_123', state=state_data)

            mock_request.redirect.assert_called_once()
            redirect_url = mock_request.redirect.call_args[0][0]
            self.assertTrue(redirect_url.startswith('https://odoo.example.com/auth_oauth/signin?'))
            parsed = urlparse(redirect_url)
            qs = parse_qs(parsed.query)
            self.assertEqual(qs.get('access_token'), ['oauth_code_123'])
            self.assertEqual(qs.get('provider'), [str(self.provider.id)])

    def test_callback_handler_user_denied_access(self):
        """Test callback redirection when user cancels on GitHub."""
        handler = CallbackHandler()
        mock_request = MagicMock()
        mock_request.redirect.side_effect = lambda url, code=302: Response('redirect', status=code)

        with patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.request', mock_request):
            handler.get_oauth_token(error='access_denied', error_description='The user has denied access.')
            mock_request.redirect.assert_called_once_with('/web/login?oauth_error=2', 303)

    def test_callback_handler_other_error(self):
        """Test callback redirection when provider returns an error."""
        handler = CallbackHandler()
        mock_request = MagicMock()
        mock_request.redirect.side_effect = lambda url, code=302: Response('redirect', status=code)

        with patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.request', mock_request):
            handler.get_oauth_token(error='server_error', error_description='Internal server error.')
            mock_request.redirect.assert_called_once_with('/web/login?oauth_error=5', 303)

    def test_callback_handler_missing_credentials(self):
        """Test callback redirection when client credentials are missing."""
        handler = CallbackHandler()
        provider_no_cred = self.env['auth.oauth.provider'].create({
            'name': 'GitHub Provider Without Credentials',
            'body': 'Log in with GitHub',
            'client_id': False,
            'client_secret': False,
            'auth_endpoint': 'https://github.com/login/oauth/authorize',
            'validation_endpoint': 'https://github.com/login/oauth/access_token',
        })

        mock_request = MagicMock()
        mock_request.httprequest.url_root = 'https://odoo.example.com/'
        mock_request.env = self.env
        mock_request.redirect.side_effect = lambda url, code=302: Response('redirect', status=code)

        with patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.request', mock_request):
            state_data = json.dumps({'p': provider_no_cred.id})
            handler.get_oauth_token(code='oauth_code_123', state=state_data)

            mock_request.redirect.assert_called_once_with('/web/login?oauth_error=6', 303)

    def test_callback_handler_missing_code(self):
        """Test callback redirection when code parameter is missing."""
        handler = CallbackHandler()
        mock_request = MagicMock()
        mock_request.httprequest.url_root = 'https://odoo.example.com/'
        mock_request.env = self.env
        mock_request.redirect.side_effect = lambda url, code=302: Response('redirect', status=code)

        with patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.request', mock_request):
            state_data = json.dumps({'p': self.provider.id})
            handler.get_oauth_token(state=state_data)

            mock_request.redirect.assert_called_once_with('/web/login?oauth_error=4', 303)

    def test_callback_handler_invalid_state(self):
        """Test callback redirection when state parameter is invalid JSON."""
        handler = CallbackHandler()
        mock_request = MagicMock()
        mock_request.httprequest.url_root = 'https://odoo.example.com/'
        mock_request.env = self.env
        mock_request.redirect.side_effect = lambda url, code=302: Response('redirect', status=code)

        with patch('odoo.addons.github_login_odoo.controllers.github_login_odoo.request', mock_request):
            handler.get_oauth_token(code='some_code', state='not-json-valid')

            mock_request.redirect.assert_called_once_with('/web/login?oauth_error=4', 303)
