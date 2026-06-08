# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import logging
import requests
import werkzeug
from odoo import _, api, fields, models
from odoo.addons.auth_signup.models.res_partner import SignupError
from odoo.exceptions import AccessDenied
from odoo.tools.misc import ustr

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """Inherit res.users model to add fields"""
    _inherit = 'res.users'

    oauth_token = fields.Char(readonly=True)
    git_username = fields.Char(default="No username",help="Username")
    git_email = fields.Char(string="Github Email",help="Email")

    def _auth_oauth_rpc(self, endpoint, access_token):
        """
            Perform an OAuth RPC call to the specified endpoint with the
            provided access token.
        """
        if self.env.context.get('github'):
            _logger.info("GitHub OAuth: Starting RPC for endpoint %s", endpoint)
            provider = self.env['auth.oauth.provider'].browse(self.env.context.get('provider'))
            
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
                _logger.error("GitHub OAuth: Token exchange failed with status %s: %s", response.status_code, response.text)
                return {'error': 'token_exchange_failed'}

            try:
                data = response.json()
            except Exception:
                _logger.error("GitHub OAuth: Failed to parse GitHub response as JSON: %s", response.text)
                return {'error': 'invalid_response_format'}

            if data.get('error'):
                _logger.error("GitHub OAuth: Error from GitHub: %s (%s)", data.get('error'), data.get('error_description'))
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
            
            _logger.info("GitHub OAuth: Successfully fetched data for user %s", user_data.get('login'))

            return {
                'key': auth_token,
                'user_id': user_data.get('id'),
                'username': user_data.get('login'),
                'name': user_data.get('name') or user_data.get('login'),
                'email': primary_email
            }

        else:
            # Standard OAuth RPC Logic
            if (self.env['ir.config_parameter'].sudo().
                    get_param('auth_oauth.authorization_header')):
                response = requests.get(endpoint,
                                        headers={'Authorization': 'Bearer %s'
                                                % access_token}, timeout=10)
            else:
                response = requests.get(endpoint,
                                        params={'access_token': access_token},
                                        timeout=10)
            if response.ok:
                return response.json()
            
            # Handle WWW-Authenticate header
            # Odoo 19 core uses a helper or direct parsing
            auth_challenge = response.headers.get('WWW-Authenticate')
            if auth_challenge and 'bearer' in auth_challenge.lower() and 'error' in auth_challenge.lower():
                # Basic parsing if needed, but core usually handles it
                return {'error': 'invalid_token'}
            
            return {'error': 'invalid_request'}

    @api.model
    def auth_oauth(self, provider, params):
        """
            Retrieve and sign in the user for GitHub OAuth.
            We override this to use the real access token instead of the 'code'.
        """
        if self.env.context.get('github'):
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

        return super(ResUsers, self).auth_oauth(provider, params)

    @api.model
    def _auth_oauth_validate(self, provider, access_token):
        """
            Validate the OAuth access token with the specified provider and
            retrieve user data.

            This method validates the provided OAuth access token with the
            given provider's validation endpoint.
            If validation is successful, it retrieves additional user data from
             the provider's data endpoint.
            It then processes the validation response to extract the user's
            subject identity and returns the validation
            data.
        """
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        validation = self._auth_oauth_rpc(oauth_provider.validation_endpoint,
                                          access_token)
        if validation.get("error"):
            raise Exception(validation['error'])
        if oauth_provider.data_endpoint:
            data = self._auth_oauth_rpc(oauth_provider.data_endpoint,
                                        access_token)
            validation.update(data)
        if self.env.context.get('github'):
            return validation
        subject = next(filter(None, [
            validation.pop(key, None)
            for key in [
                'sub',
                'id',
                'user_id',
            ]
        ]), None)
        if not subject:
            raise AccessDenied('Missing subject identity')
        validation['user_id'] = subject

        return validation

    def github_api_hit(self):
        """
            Trigger GitHub OAuth authorization by redirecting to GitHub's
            authorization URL.

            This method retrieves the GitHub OAuth provider configuration and
            constructs the authorization URL.
            It checks if the client ID is available and redirects the user to
            GitHub's authorization page.
            The authorization URL includes the required client ID and scopes
            (repo and user) for the OAuth request.
        """
        provider = self.env.ref('github_login_odoo.auth_oauth_provider_github')
        provider = self.env[provider._name].sudo().browse(provider.id)
        if provider:
            if not provider.client_id:
                r_url = "/web/login?oauth_error=6"
                _logger.info(
                    'OAuth2: Either of Client ID or Client Secret not present, '
                    'access denied, redirect to main page in case a valid '
                    'session exists, without setting cookies')
                redirect = werkzeug.utils.redirect(r_url, 303)
                redirect.autocorrect_location_header = False
                return redirect
            url = ("https://github.com/login/oauth/authorize?client_id=%s&"
                   "scope=repo,user") % provider.client_id
            response = requests.get(url)
            if response.status_code in [200, 201]:
                return response.url

    @api.model
    def _signup_create_user(self, values):
        """
            Create a new user during signup using the default method.

            This method calls the default user creation method during signup.
            It simply delegates the user creation process to the parent class
            method.
        """
        return super(ResUsers, self)._signup_create_user(values)

    def _create_user_from_default_template(self, values):
        """
            Create a new user based on the default user template.

            This method creates a new user by copying the default user template.
            It validates the provided values and ensures that essential fields
             like login, name, and partner are
            provided.
            If the template user does not exist or the required values are
            missing, it raises appropriate exceptions.
        """
        template_user = self.env.ref('base.default_user')
        if not template_user.exists():
            raise ValueError(_('Signup: invalid template user'))
        if not values.get('login'):
            raise ValueError(_('Signup: no login given for new user'))
        if not values.get('partner_id') and not values.get('name'):
            raise ValueError(_('Signup: no name or partner given for new user'))
        values['active'] = True
        try:
            with ((self.env.cr.savepoint())):
                return template_user.with_context(no_reset_password=True
                                                  ).copy(values)
        except Exception as e:
            # copy may fail if asked login is not available.
            raise SignupError(ustr(e))
