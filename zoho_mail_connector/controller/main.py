# -*- coding: utf-8 -*-
#############################################################################
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
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3 for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import datetime
from html import escape
import logging

import requests
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class ZohoOAuthController(http.Controller):
    @staticmethod
    def _json_response(response):
        """Return response JSON, falling back to raw text for diagnostics."""
        try:
            return response.json()
        except ValueError:
            return {'raw_response': response.text}

    @staticmethod
    def _build_error_message(title, response=None, data=None):
        """Build a concise error message safe to show on the config form."""
        details = []
        if response is not None:
            details.append(f"HTTP {response.status_code}")
        if isinstance(data, dict):
            status = data.get('status')
            if isinstance(status, dict):
                status_details = " ".join(
                    str(status.get(key))
                    for key in ('code', 'description')
                    if status.get(key)
                )
                if status_details:
                    details.append(f"status: {status_details}")
            nested_data = data.get('data')
            if isinstance(nested_data, dict):
                for key in ('moreInfo', 'message', 'error', 'code', 'msg'):
                    value = nested_data.get(key)
                    if value:
                        details.append(f"{key}: {value}")
            for key in ('error', 'error_description', 'message', 'code'):
                value = data.get(key)
                if value:
                    details.append(f"{key}: {value}")
            raw_response = data.get('raw_response')
            if raw_response:
                details.append(raw_response[:500])
        elif data:
            details.append(str(data)[:500])
        return f"{title}: {' | '.join(details)}" if details else title

    @staticmethod
    def _mail_setup_hint(message):
        """Return a useful Zoho Mail setup hint for known vague API failures."""
        if 'USERNAME_NOT_SET' in message:
            return (
                "Zoho says USERNAME_NOT_SET. Log in to Zoho Mail and finish "
                "creating the mailbox/email username for this Zoho user, then "
                "connect again."
            )
        if 'Zoho account fetch failed' in message and 'Internal Error' in message:
            return (
                "Zoho accepted OAuth but did not return a Mail account. Log in "
                "to https://mail.zoho.in with the same Zoho user and confirm "
                "that the mailbox is created/active and the user has permission "
                "to access Zoho Mail APIs."
            )
        return False

    def _failure_response(self, account, message):
        """Persist the failure and show it immediately in the browser."""
        _logger.error(message)
        if account and account.exists():
            account.write({'state': 'error'})
            account._set_connection_error(message)
        hint = self._mail_setup_hint(message)
        body = f"""
            <html>
                <head><title>Zoho Mail Connection Failed</title></head>
                <body style="font-family: sans-serif; padding: 32px;">
                    <h2>Zoho Mail connection failed</h2>
                    <p>{escape(message)}</p>
                    {f'<p><strong>Fix:</strong> {escape(hint)}</p>' if hint else ''}
                    <p><a href="/web">Back to Odoo</a></p>
                </body>
            </html>
        """
        return request.make_response(
            body,
            headers=[('Content-Type', 'text/html; charset=utf-8')]
        )

    @http.route('/zoho_mail/oauth/callback', type='http', auth='public',
                csrf=False)
    def oauth_callback(self, **kwargs):
        """Controller for connecting the Zoho Mail account"""
        code = kwargs.get('code')
        state = kwargs.get('state')
        error = kwargs.get('error')
        if error:
            _logger.error("Zoho OAuth error: %s", error)
            return request.redirect('/web')
        if not code or not state:
            _logger.warning("Zoho OAuth callback missing code or state")
            return request.redirect('/web')
        account = request.env['zoho.mail.account'].sudo()
        try:
            account = account.browse(int(state))
            if not account.exists():
                _logger.error("Zoho account not found for state: %s", state)
                return request.redirect('/web')
            region = account.zoho_region
            # Exchange authorisation code for tokens
            token_response = requests.post(
                f"https://accounts.zoho.{region}/oauth/v2/token",
                data={
                    'grant_type': 'authorization_code',
                    'client_id': account.client_id,
                    'client_secret': account.client_secret,
                    'redirect_uri': account.redirect_uri,
                    'code': code,
                },
                timeout=30,
            )
            _logger.info("Token response status: %s", token_response.status_code)
            token_data = self._json_response(token_response)
            if token_response.status_code != 200 or token_data.get('error'):
                error_message = self._build_error_message(
                    "Zoho token exchange failed", token_response, token_data)
                return self._failure_response(account, error_message)
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in', 3600)
            if not access_token:
                error_message = self._build_error_message(
                    "Zoho did not return an access token", data=token_data)
                return self._failure_response(account, error_message)
            account.write({
                "access_token": access_token,
                "refresh_token": refresh_token or account.refresh_token,
                "token_expiry": (
                    fields.Datetime.now()
                    + datetime.timedelta(seconds=int(expires_in) - 300)
                ),
            })
            # Fetch Zoho Mail account info
            headers = {
                "Authorization": f"Zoho-oauthtoken {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            account_response = requests.get(
                f"https://mail.zoho.{region}/api/accounts",
                headers=headers,
                timeout=30,
            )
            _logger.info("Account response status: %s",
                         account_response.status_code)
            if account_response.status_code != 200:
                account_data = self._json_response(account_response)
                error_message = self._build_error_message(
                    "Zoho account fetch failed", account_response,
                    account_data)
                return self._failure_response(account, error_message)
            account_data = self._json_response(account_response)
            data_list = account_data.get('data', [])
            if not data_list:
                error_message = self._build_error_message(
                    "Zoho did not return mail account data",
                    data=account_data)
                return self._failure_response(account, error_message)
            mail_account = data_list[0]
            account.write({
                'account_id': mail_account.get('accountId'),
                'email_address': mail_account.get('mailboxAddress'),
                'state': 'connected',
            })
            account._set_connection_error(False)
            account.action_fetch_folders(access_token)
        except Exception as e:
            error_message = f"Zoho OAuth callback failed: {str(e)}"
            _logger.exception(error_message)
            return self._failure_response(account, error_message)
        return request.redirect('/web')
