# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
import datetime

import requests
import logging
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class ZohoOAuthController(http.Controller):
    @http.route('/zoho_mail/oauth/callback', type='http', auth='public', csrf=False)
    def oauth_callback(self, **kwargs):
        """Controller for connecting the Zoho Mail account"""
        code = kwargs.get('code')
        state = kwargs.get('state')
        if not code:
            return request.redirect('/web')
        account = request.env['zoho.mail.account'].sudo().browse(int(state))
        region = account.zoho_region
        token_response = requests.post(
            f"https://accounts.zoho.{region}/oauth/v2/token",
            data={
                'grant_type': 'authorization_code',
                'client_id': account.client_id,
                'client_secret': account.client_secret,
                'redirect_uri': account.redirect_uri,
                'code': code,
            },
            timeout=30
        )
        token_data = token_response.json()
        refresh_token = token_data.get('refresh_token')
        access_token = token_data.get('access_token')
        expires_in = token_data.get('expires_in', 3600)
        account.write({
            'refresh_token': refresh_token,
            'access_token': access_token,
            'token_expiry': fields.Datetime.now() +
                    datetime.timedelta(seconds=expires_in - 300),
        })
        headers = {
            "Authorization":
                f"Zoho-oauthtoken {access_token}"
        }
        account_response = requests.get(
            f"https://mail.zoho.{region}/api/accounts",
            headers=headers,
            timeout=30
        )
        account_data = account_response.json()

        if account_response.status_code != 200:
            account.write({'state': 'error'})
            _logger.error(f"Zoho Account API failed: {account_data}")
            return request.redirect('/web')

        if not isinstance(account_data.get('data'), list):
            account.write({'state': 'error'})
            _logger.error(f"Unexpected Zoho account response: {account_data}")
            return request.redirect('/web')

        if not account_data.get('data'):
            account.write({'state': 'error'})
            _logger.error("No Zoho Mail account was returned.")
            return request.redirect('/web')

        mail_account = account_data['data'][0]
        account.write({
            'account_id': mail_account['accountId'],
            'email_address': mail_account['mailboxAddress'],
            'state': 'connected'
        })
        account.action_fetch_folders(access_token)
        return request.redirect('/web')
