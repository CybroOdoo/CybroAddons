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
import logging
import requests
from odoo import api, models
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """Inherit res.users model for GitHub OAuth integration."""
    _inherit = 'res.users'

    def _auth_oauth_rpc(self, endpoint, access_token):
        """
        Perform an OAuth RPC call to the specified endpoint with the
        provided access token.
        """
        if self.env.context.get('github'):
            _logger.info("GitHub OAuth: Starting RPC for endpoint %s", endpoint)
            provider_id = self.env.context.get('provider')
            provider = self.env['auth.oauth.provider'].browse(provider_id) if provider_id else None
            if not provider or not provider.exists():
                _logger.error("GitHub OAuth: Provider not found in context: %s", provider_id)
                return {'error': 'provider_not_found'}

            # 1. Exchange 'code' for 'access_token'
            # GitHub documentation recommends a POST request for this.
            params = {
                'client_id': provider.client_id,
                'client_secret': provider.client_secret,
                'code': access_token,
            }
            # Requesting JSON response from GitHub
            headers = {'Accept': 'application/json'}
            _logger.info("GitHub OAuth: Exchanging code for token...")
            response = requests.post(endpoint, data=params, headers=headers, timeout=10)
            if not response.ok:
                _logger.error(
                    "GitHub OAuth: Token exchange failed with status %s: %s",
                    response.status_code, response.text
                )
                return {'error': 'token_exchange_failed'}
            try:
                data = response.json()
            except Exception:
                _logger.error("GitHub OAuth: Failed to parse GitHub response as JSON: %s", response.text)
                return {'error': 'invalid_response_format'}
            if data.get('error'):
                _logger.error(
                    "GitHub OAuth: Error from GitHub: %s (%s)",
                    data.get('error'), data.get('error_description')
                )
                return {'error': data.get('error')}
            auth_token = data.get('access_token')
            if not auth_token:
                _logger.error("GitHub OAuth: No access_token in GitHub response: %s", data)
                return {'error': 'no_access_token'}

            _logger.info("GitHub OAuth: Successfully obtained access token.")

            # 2. Get User Emails
            headers = {
                'Authorization': f'Bearer {auth_token}',
                'Accept': 'application/vnd.github+json',
            }
            _logger.info("GitHub OAuth: Fetching user emails...")
            emails_response = requests.get('https://api.github.com/user/emails', headers=headers, timeout=10)
            if not emails_response.ok:
                _logger.error("GitHub OAuth: Failed to fetch emails: %s", emails_response.text)
                return {'error': 'email_fetch_failed'}
            emails_data = emails_response.json()
            primary_email = next((e['email'] for e in emails_data if e.get('primary')), None)
            if not primary_email and emails_data:
                primary_email = emails_data[0]['email']

            # 3. Get User Profile Data
            _logger.info("GitHub OAuth: Fetching user profile...")
            user_response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
            if not user_response.ok:
                _logger.error("GitHub OAuth: Failed to fetch user profile: %s", user_response.text)
                return {'error': 'profile_fetch_failed'}
            user_data = user_response.json()
            _logger.debug("GitHub OAuth: Successfully fetched data for user id %s", user_data.get('id'))
            return {
                'key': auth_token,
                'user_id': user_data.get('id'),
                'username': user_data.get('login'),
                'name': user_data.get('name') or user_data.get('login'),
                'email': primary_email
            }
        return super()._auth_oauth_rpc(endpoint, access_token)

    @api.model
    def auth_oauth(self, provider, params):
        """
        Retrieve and sign in the user for GitHub OAuth.
        We override this to use the real access token instead of the 'code'.
        Non-GitHub providers use standard core auth_oauth flow.
        """
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        if (oauth_provider.exists() and oauth_provider.is_github) or self.env.context.get('github'):
            self = self.with_context(provider=provider, github=True)
            access_token = params.get('access_token')
            validation = self._auth_oauth_validate(provider, access_token)

            # GitHub returns the real token in 'key'
            real_token = validation.get('key')
            if real_token:
                # Update params so _auth_oauth_signin stores the real token
                params['access_token'] = real_token

            # retrieve and sign in user
            login = self._auth_oauth_signin(provider, validation, params)
            if not login:
                raise AccessDenied()
            return (self.env.cr.dbname, login, real_token or access_token)

        return super().auth_oauth(provider, params)

    @api.model
    def _auth_oauth_validate(self, provider, access_token):
        """
        Validate the OAuth access token with the specified provider and
        retrieve user data.
        Non-GitHub providers use standard core _auth_oauth_validate flow.
        """
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        if (oauth_provider.exists() and oauth_provider.is_github) or self.env.context.get('github'):
            self = self.with_context(provider=provider, github=True)
            validation = self._auth_oauth_rpc(oauth_provider.validation_endpoint, access_token)
            if validation.get("error"):
                raise AccessDenied(validation['error'])
            if oauth_provider.data_endpoint:
                data = self._auth_oauth_rpc(oauth_provider.data_endpoint, access_token)
                validation.update(data)
            return validation
        return super()._auth_oauth_validate(provider, access_token)
