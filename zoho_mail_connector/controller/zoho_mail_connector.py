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
import datetime
import requests
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import UserError


class ZohoOAuthController(http.Controller):
    """Controller for connecting the Zoho Mail account"""

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

        if token_response.status_code != 200:
            return request.redirect('/web')

        token_data = token_response.json()

        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')

        if not access_token:
            raise UserError(
                f"Access token was not returned by Zoho: {token_data}"
            )

        expires_in = token_data.get('expires_in', 3600)

        account.write({
            'refresh_token': refresh_token,
            'access_token': access_token,
            'token_expiry': fields.Datetime.now() +
                            datetime.timedelta(seconds=expires_in - 300),
        })

        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}"
        }

        account_url = f"https://mail.zoho.{region}/api/accounts"

        account_response = requests.get(
            account_url,
            headers=headers,
            timeout=30
        )

        if account_response.status_code != 200:
            raise UserError(
                f"Zoho Mail account API failed.\n"
                f"Status: {account_response.status_code}\n"
                f"Response: {account_response.text}"
            )

        account_data = account_response.json()

        data = account_data.get('data')

        if not isinstance(data, list) or not data:
            raise UserError(
                f"Unexpected Zoho account response:\n{account_data}"
            )

        mail_account = data[0]

        account.write({
            'account_id': mail_account.get('accountId'),
            'email_address': mail_account.get('mailboxAddress'),
            'state': 'connected'
        })

        account.action_fetch_folders(access_token)

        return request.redirect('/web')
