# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import logging
import requests
import werkzeug
from odoo import api, fields, models
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """Inherit res.users model to add GitHub OAuth fields and authentication."""

    _inherit = 'res.users'

    # Fields declarations
    oauth_token = fields.Char(
        string="OAuth Token",
        help="OAuth access token for the authenticated user.",
        readonly=True)
    git_username = fields.Char(
        string="GitHub Username",
        default="No username",
        help="GitHub username of the authenticated user.")
    git_email = fields.Char(
        string="GitHub Email",
        help="Primary email address associated with the GitHub account.")

    # CRUD methods
    @api.model
    def _signup_create_user(self, values):
        """Create a new user during signup.

        Override to forcefully create users as Portal Users when they
        sign up via GitHub OAuth.
        """
        if self.env.context.get('github'):
            portal_group = self.env.ref(
                'base.group_portal', raise_if_not_found=False)
            if portal_group:
                values['groups_id'] = [(6, 0, [portal_group.id])]
        return super(ResUsers, self)._signup_create_user(values)

    # Action methods
    def action_github_api_hit(self):
        """Trigger GitHub OAuth authorization by redirecting to GitHub's authorization URL.

        Retrieves the GitHub OAuth provider configuration and constructs the
        authorization URL. Checks if the client ID is available and redirects
        the user to GitHub's authorization page with the required scopes.
        """
        provider = self.env.ref('github_login_odoo.auth_oauth_provider_github')
        provider = self.env[provider._name].sudo().browse(provider.id)
        if not provider.client_id:
            _logger.info(
                'OAuth2: Client ID not present, access denied, redirecting '
                'to login page.')
            r_url = "/web/login?oauth_error=6"
            redirect = werkzeug.utils.redirect(r_url, 303)
            redirect.autocorrect_location_header = False
            return redirect
        url = ("https://github.com/login/oauth/authorize"
               "?client_id=%s&scope=repo,user") % provider.client_id
        response = requests.get(url)
        if response.status_code in [200, 201]:
            return response.url

    # Business methods
    def _auth_oauth_rpc(self, endpoint, access_token):
        """Perform an OAuth RPC call to the specified endpoint with the provided access token.

        For GitHub, exchanges the authorization code for a real access token,
        then fetches the user's email and profile data.
        For standard OAuth providers, performs a GET request with the token.
        """
        if self.env.context.get('github'):
            _logger.info(
                "GitHub OAuth: Starting RPC for endpoint %s", endpoint)
            provider = self.env['auth.oauth.provider'].browse(
                self.env.context.get('provider'))

            # Exchange 'code' for 'access_token'
            params = {
                'client_id': provider.client_id,
                'client_secret': provider.client_secret,
                'code': access_token,
            }
            headers = {'Accept': 'application/json'}
            _logger.info("GitHub OAuth: Exchanging code for token...")
            response = requests.post(
                endpoint, data=params, headers=headers, timeout=10)

            if not response.ok:
                _logger.error(
                    "GitHub OAuth: Token exchange failed with status %s: %s",
                    response.status_code, response.text)
                return {'error': 'token_exchange_failed'}

            try:
                data = response.json()
            except Exception:
                _logger.error(
                    "GitHub OAuth: Failed to parse GitHub response as JSON: %s",
                    response.text)
                return {'error': 'invalid_response_format'}

            if data.get('error'):
                _logger.error(
                    "GitHub OAuth: Error from GitHub: %s (%s)",
                    data.get('error'), data.get('error_description'))
                return {'error': data.get('error')}

            auth_token = data.get('access_token')
            if not auth_token:
                _logger.error(
                    "GitHub OAuth: No access_token in GitHub response: %s",
                    data)
                return {'error': 'no_access_token'}

            _logger.info("GitHub OAuth: Successfully obtained access token.")

            # Fetch user emails
            headers = {
                'Authorization': 'Bearer {}'.format(auth_token),
                'Accept': 'application/vnd.github+json',
            }
            _logger.info("GitHub OAuth: Fetching user emails...")
            emails_response = requests.get(
                'https://api.github.com/user/emails',
                headers=headers, timeout=10)
            if not emails_response.ok:
                _logger.error(
                    "GitHub OAuth: Failed to fetch emails: %s",
                    emails_response.text)
                return {'error': 'email_fetch_failed'}

            emails_data = emails_response.json()
            primary_email = next(
                (e['email'] for e in emails_data if e.get('primary')), None)
            if not primary_email and emails_data:
                primary_email = emails_data[0]['email']

            # Fetch user profile
            _logger.info("GitHub OAuth: Fetching user profile...")
            user_response = requests.get(
                'https://api.github.com/user', headers=headers, timeout=10)
            if not user_response.ok:
                _logger.error(
                    "GitHub OAuth: Failed to fetch user profile: %s",
                    user_response.text)
                return {'error': 'profile_fetch_failed'}

            user_data = user_response.json()
            _logger.info(
                "GitHub OAuth: Successfully fetched data for user %s",
                user_data.get('login'))

            return {
                'key': auth_token,
                'user_id': user_data.get('id'),
                'username': user_data.get('login'),
                'name': user_data.get('name') or user_data.get('login'),
                'email': primary_email,
            }

        # Standard OAuth RPC logic
        if (self.env['ir.config_parameter'].sudo().
                get_param('auth_oauth.authorization_header')):
            response = requests.get(
                endpoint,
                headers={'Authorization': 'Bearer %s' % access_token},
                timeout=10)
        else:
            response = requests.get(
                endpoint,
                params={'access_token': access_token},
                timeout=10)

        if response.ok:
            return response.json()

        auth_challenge = response.headers.get('WWW-Authenticate')
        if (auth_challenge and 'bearer' in auth_challenge.lower()
                and 'error' in auth_challenge.lower()):
            return {'error': 'invalid_token'}

        return {'error': 'invalid_request'}

    @api.model
    def _auth_oauth_validate(self, provider, access_token):
        """Validate the OAuth access token with the specified provider and retrieve user data.

        Validates the provided OAuth access token with the given provider's
        validation endpoint. If validation is successful, retrieves additional
        user data from the provider's data endpoint, then extracts the user's
        subject identity and returns the validation data.
        """
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        validation = self._auth_oauth_rpc(
            oauth_provider.validation_endpoint, access_token)
        if validation.get("error"):
            raise Exception(validation['error'])
        if oauth_provider.data_endpoint:
            data = self._auth_oauth_rpc(
                oauth_provider.data_endpoint, access_token)
            validation.update(data)
        if self.env.context.get('github'):
            return validation
        subject = next(filter(None, [
            validation.pop(key, None)
            for key in ['sub', 'id', 'user_id']
        ]), None)
        if not subject:
            raise AccessDenied('Missing subject identity')
        validation['user_id'] = subject
        return validation

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        """Override the standard auth_oauth_signin to link existing users by email.

        Links existing users based on their email address if they don't
        already have an oauth_uid assigned.
        """
        if self.env.context.get('github'):
            oauth_uid = validation.get('user_id')
            email = validation.get('email')
            if oauth_uid and email:
                oauth_user = self.search([
                    ("oauth_uid", "=", oauth_uid),
                    ('oauth_provider_id', '=', provider),
                ])
                if not oauth_user:
                    existing_user = self.search(
                        [('login', '=', email)], limit=1)
                    if not existing_user:
                        existing_user = self.search(
                            [('email', '=', email)], limit=1)
                    if existing_user:
                        existing_user.sudo().write({
                            'oauth_provider_id': provider,
                            'oauth_uid': oauth_uid,
                            'oauth_access_token': params.get('access_token'),
                        })
                        return existing_user.login
        return super(ResUsers, self)._auth_oauth_signin(
            provider, validation, params)

    @api.model
    def auth_oauth(self, provider, params):
        """Retrieve and sign in the user for GitHub OAuth.

        Overrides the standard auth_oauth to use the real GitHub access token
        instead of the authorization code received in the callback.
        """
        if self.env.context.get('github'):
            access_token = params.get('access_token')
            validation = self._auth_oauth_validate(provider, access_token)
            real_token = validation.get('key')
            if real_token:
                params['access_token'] = real_token
            login = self._auth_oauth_signin(provider, validation, params)
            if not login:
                raise AccessDenied()
            return (self.env.cr.dbname, login, real_token or access_token)
        return super(ResUsers, self).auth_oauth(provider, params)
