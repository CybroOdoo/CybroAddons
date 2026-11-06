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
from urllib.parse import urlencode

import requests

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import hmac

TIMEOUT = 20
AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
TASKS_URL = 'https://tasks.googleapis.com/tasks/v1/lists/@default/tasks'
TASKS_SCOPE = 'https://www.googleapis.com/auth/tasks'
REDIRECT_PATH = '/google_task_authentication'


class ProjectCredential(models.Model):
    """Google API credentials used to sync project tasks with Google Tasks"""
    _name = 'project.credential'
    _description = 'Google Task Credentials'

    name = fields.Char(default='Credentials',
                       help='Name of the credentials')
    hangout_client = fields.Char(string='Client ID',
                                 help='Google Cloud Console Client ID')
    hangout_client_secret = fields.Char(string='Client Secret',
                                        help='Google Cloud Console Client '
                                             'Secret')
    hangout_redirect_uri = fields.Char(
        string='Authorized redirect URIs',
        default=lambda self: self._default_redirect_uri(),
        help='Redirect URI added to the OAuth client in Google Cloud Console')
    hangout_company_access_token = fields.Char(
        string='Access Token', copy=False,
        help='Access token for the Google Tasks API')
    hangout_company_access_token_expiry = fields.Datetime(
        string='Token Expiry', copy=False,
        help='Expiry date and time of the access token')
    hangout_company_refresh_token = fields.Char(
        string='Refresh Token', copy=False,
        help='Refresh token for the Google Tasks API')
    hangout_company_authorization_code = fields.Char(
        string='Authorization Code', copy=False,
        help='Last authorization code received from Google')

    def _default_redirect_uri(self):
        """Odoo URL followed by the authentication route"""
        return self.env['ir.config_parameter'].sudo().get_str(
            'web.base.url') + REDIRECT_PATH

    def _get_oauth_state(self):
        """Signed state passed to Google and checked on the way back"""
        return hmac(self.env(su=True), 'google_tasks_oauth', self.env.uid)

    def action_google_task_company_authenticate(self):
        """Open the Google consent screen"""
        self.ensure_one()
        if not self.hangout_client:
            raise UserError(self.env._('Please enter the Client ID.'))
        if not self.hangout_client_secret:
            raise UserError(self.env._('Please enter the Client Secret.'))
        if not self.hangout_redirect_uri:
            raise UserError(
                self.env._('Please enter the Authorized redirect URI.'))
        params = {
            'response_type': 'code',
            'client_id': self.hangout_client,
            'redirect_uri': self.hangout_redirect_uri,
            'scope': TASKS_SCOPE,
            'access_type': 'offline',
            # Google only returns a refresh token on consent
            'prompt': 'consent',
            'state': self._get_oauth_state(),
        }
        return {
            'type': 'ir.actions.act_url',
            'url': f'{AUTH_URL}?{urlencode(params)}',
            'target': 'new',
        }

    def _request_token(self, data):
        """Call the Google token endpoint and store the tokens it returns"""
        self.ensure_one()
        data = dict(data, client_id=self.hangout_client,
                    client_secret=self.hangout_client_secret)
        try:
            response = requests.post(TOKEN_URL, data=data, timeout=TIMEOUT)
            result = response.json()
        except (requests.RequestException, ValueError) as error:
            raise UserError(
                self.env._('Could not reach Google: %s', error)) from error
        if not result.get('access_token'):
            raise UserError(self.env._(
                'Google did not return an access token: %s',
                result.get('error_description') or result.get('error')
                or response.text))
        vals = {
            'hangout_company_access_token': result['access_token'],
            'hangout_company_access_token_expiry':
                fields.Datetime.now() + timedelta(
                    seconds=result.get('expires_in', 3600)),
        }
        if result.get('refresh_token'):
            vals['hangout_company_refresh_token'] = result['refresh_token']
        self.write(vals)

    def _exchange_authorization_code(self, code):
        """Turn the authorization code from Google into tokens"""
        self.ensure_one()
        self.hangout_company_authorization_code = code
        self._request_token({
            'code': code,
            'redirect_uri': self.hangout_redirect_uri,
            'grant_type': 'authorization_code',
        })

    def _refresh_access_token(self):
        """Get a new access token with the refresh token"""
        self.ensure_one()
        if not self.hangout_client or not self.hangout_client_secret:
            raise UserError(self.env._('The Google Task credentials are '
                                       'not configured yet.'))
        if not self.hangout_company_refresh_token:
            raise UserError(self.env._('No refresh token yet: click '
                                       'Authenticate first.'))
        self._request_token({
            'refresh_token': self.hangout_company_refresh_token,
            'grant_type': 'refresh_token',
        })

    def action_google_task_company_refresh_token(self):
        """Refresh the access token from the credentials form"""
        self._refresh_access_token()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Success'),
                'message': self.env._('Token refreshed successfully!'),
                'type': 'success',
                'sticky': False,
            },
        }

    def _get_access_token(self):
        """Return a valid access token, refreshing it when it has expired"""
        self.ensure_one()
        if (not self.hangout_company_access_token
                or not self.hangout_company_access_token_expiry
                or self.hangout_company_access_token_expiry
                <= fields.Datetime.now() + timedelta(minutes=1)):
            self._refresh_access_token()
        return self.hangout_company_access_token

    def _google_tasks_request(self, method, path='', **kwargs):
        """Send a request to the Google Tasks API (default task list)"""
        self.ensure_one()
        headers = {
            'Authorization': f'Bearer {self._get_access_token()}',
            'Accept': 'application/json',
        }
        try:
            return requests.request(method, TASKS_URL + path,
                                    headers=headers, timeout=TIMEOUT,
                                    **kwargs)
        except requests.RequestException as error:
            raise UserError(
                self.env._('Could not reach Google Tasks: %s', error)) from error
