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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""Single place for all Zendesk API communication.

Zendesk is retiring API tokens (email/token basic auth). This helper uses
OAuth 2.0 with the *client credentials* grant: Odoo exchanges the OAuth
client's identifier + secret for a short-lived access token and sends it
as ``Authorization: Bearer <token>``. The token is cached in
ir.config_parameter and renewed automatically when it expires.
"""
import logging
from datetime import timedelta
from urllib.parse import urlsplit

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

PARAM_PREFIX = 'odoo_zendesk_connector.'
TIMEOUT = 60


class ZendeskApi(models.AbstractModel):
    """Usage from any model:
        api = self.env['zendesk.api']
        data = api._request('GET', 'tickets.json')
        api._request('POST', 'tickets.json', json={...})
    """
    _name = 'zendesk.api'
    _description = 'Zendesk API Helper'

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    @api.model
    def _get_param(self, key, default=False):
        params = self.env['ir.config_parameter'].sudo()
        full_key = PARAM_PREFIX + key
        if key == 'is_connect_zendesk':
            return params.get_bool(full_key, default=bool(default))
        val = params.get_str(full_key, default=default)
        if val == 'False':
            return default
        return val

    @api.model
    def _set_param(self, key, value):
        params = self.env['ir.config_parameter'].sudo()
        full_key = PARAM_PREFIX + key
        if key == 'is_connect_zendesk':
            if isinstance(value, str):
                params.set_bool(full_key, value.lower() in ('true', '1', 'yes', 'on'))
            else:
                params.set_bool(full_key, bool(value))
        else:
            params.set_str(full_key, str(value) if value is not False and value is not None else None)

    @api.model
    def _is_connected(self):
        """Return True if Zendesk integration is enabled in settings."""
        return self.env['ir.config_parameter'].sudo().get_bool(
            PARAM_PREFIX + 'is_connect_zendesk')

    @api.model
    def _get_config(self):
        if not self._is_connected():
            raise UserError(_(
                "Zendesk connection is disabled. Please enable 'Connect Zendesk' "
                "in Helpdesk settings."))
        config = {
            'domain': (self._get_param('company_domain') or '').strip(),
            'client_id': (self._get_param('client_id') or '').strip(),
            'client_secret': (self._get_param('client_secret') or '').strip(),
            'scope': (self._get_param('scope') or 'read write').strip(),
        }
        missing = [label for key, label in (
            ('domain', _('Company Domain')),
            ('client_id', _('OAuth Client Identifier')),
            ('client_secret', _('OAuth Client Secret')),
        ) if not config[key]]
        if missing:
            raise UserError(_(
                "Zendesk is not configured. Please fill in: %s",
                ', '.join(missing)))
        return config

    @api.model
    def _base_url(self, domain=None):
        domain = domain or self._get_config()['domain']
        # Accept "mycompany" as well as "mycompany.zendesk.com"
        domain = domain.replace('https://', '').replace('http://', '')
        domain = domain.split('.zendesk.com')[0].strip('/')
        return f'https://{domain}.zendesk.com'

    # ------------------------------------------------------------------
    # OAuth token
    # ------------------------------------------------------------------
    @api.model
    def _fetch_access_token(self, config=None):
        """Get a new access token using the client credentials grant.
        This grant has no refresh token: when the token expires we just
        request a new one the same way."""
        config = config or self._get_config()
        url = f"{self._base_url(config['domain'])}/oauth/tokens"
        payload = {
            'grant_type': 'client_credentials',
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'scope': config['scope'],
        }
        try:
            response = requests.post(url, json=payload, timeout=TIMEOUT)
        except requests.exceptions.RequestException as error:
            raise UserError(_("Could not reach Zendesk: %s", error))
        if response.status_code != 200:
            raise UserError(_(
                "Zendesk refused the OAuth request (%(code)s): %(body)s",
                code=response.status_code, body=response.text))
        data = response.json()
        token = data.get('access_token')
        if not token:
            raise UserError(_("Zendesk did not return an access token."))
        expires_in = int(data.get('expires_in') or 1800)
        # Renew 60 seconds early so we never send an almost-expired token
        expiry = fields.Datetime.now() + timedelta(
            seconds=max(expires_in - 60, 60))
        self._set_param('access_token', token)
        self._set_param('token_expiry', fields.Datetime.to_string(expiry))
        return token

    @api.model
    def _get_access_token(self):
        token = self._get_param('access_token')
        expiry = self._get_param('token_expiry')
        if token and expiry and \
                fields.Datetime.to_datetime(expiry) > fields.Datetime.now():
            return token
        return self._fetch_access_token()

    @api.model
    def _clear_token(self):
        self._set_param('access_token', False)
        self._set_param('token_expiry', False)

    # ------------------------------------------------------------------
    # Generic request
    # ------------------------------------------------------------------
    @api.model
    @api.private
    def _raw_request(self, method, endpoint, **kwargs):
        """Call /api/v2/<endpoint> and return the requests.Response.
        ``endpoint`` may also be a full URL (e.g. a ``next_page`` link)
        strictly under the configured Zendesk base_url.
        Retries once with a new token on 401 invalid_token."""
        base_url = self._base_url()
        endpoint_str = str(endpoint or '').strip()
        if endpoint_str.startswith(('http://', 'https://')):
            # Security: ensure full URLs only target the configured Zendesk instance
            parsed_endpoint = urlsplit(endpoint_str)
            parsed_base = urlsplit(base_url)
            if (parsed_endpoint.scheme != parsed_base.scheme or
                    parsed_endpoint.netloc != parsed_base.netloc):
                raise UserError(_(
                    "Invalid Zendesk endpoint %(endpoint)s: must be under %(base_url)s",
                    endpoint=endpoint_str, base_url=base_url))
            url = endpoint_str
        else:
            url = f"{base_url}/api/v2/{endpoint_str.lstrip('/')}"
        timeout = kwargs.pop('timeout', TIMEOUT)
        extra_headers = kwargs.pop('headers', None) or {}
        response = None
        for attempt in range(2):
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self._get_access_token()}',
            }
            headers.update(extra_headers)
            try:
                response = requests.request(method, url, headers=headers,
                                            timeout=timeout, **kwargs)
            except requests.exceptions.RequestException as error:
                raise UserError(_("Could not reach Zendesk: %s", error))
            if response.status_code == 401 and attempt == 0 and \
                    'invalid_token' in response.text:
                self._clear_token()
                continue
            break
        return response

    @api.model
    @api.private
    def _request(self, method, endpoint, **kwargs):
        """Same as _raw_request, but raises a UserError on failure and
        returns the decoded JSON body ({} for empty bodies, e.g. 204)."""
        response = self._raw_request(method, endpoint, **kwargs)
        if not response.ok:
            _logger.warning("Zendesk %s %s failed: %s %s", method, endpoint,
                            response.status_code, response.text)
            raise UserError(_(
                "Zendesk returned an error (%(code)s): %(body)s",
                code=response.status_code, body=self._error_text(response)))
        return response.json() if response.content else {}

    @api.model
    def _error_text(self, response):
        try:
            data = response.json()
        except ValueError:
            return response.text
        error = data.get('error')
        if isinstance(error, dict):
            error = error.get('message') or error.get('title')
        return data.get('description') or error or response.text

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    @api.model
    @api.private
    def _find_or_create_user(self, name, email):
        """Return the Zendesk user id for this email, creating the user if
        it does not exist yet."""
        if not email:
            raise UserError(_("An email is required to sync with Zendesk."))
        result = self._request('GET', 'users/search.json',
                               params={'query': f'email:{email}'})
        users = result.get('users') or []
        if users:
            return users[0]['id']
        result = self._request('POST', 'users.json', json={
            'user': {'name': name or email, 'email': email}})
        return result['user']['id']

    @api.model
    def notify(self, title, message, notif_type='info', sticky=False):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': notif_type,
                'sticky': sticky,
            },
        }


# Priority mapping between Odoo helpdesk ('0'-'4') and Zendesk
ODOO_TO_ZENDESK_PRIORITY = {
    '1': 'low',
    '2': 'normal',
    '3': 'high',
    '4': 'urgent',
}
ZENDESK_TO_ODOO_PRIORITY = {v: k for k, v in ODOO_TO_ZENDESK_PRIORITY.items()}
