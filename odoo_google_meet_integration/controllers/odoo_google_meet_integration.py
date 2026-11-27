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

import datetime
import hmac
import requests
from odoo import http
from odoo.exceptions import UserError
from odoo.http import request

TIMEOUT = 20


class GoogleMeetAuth(http.Controller):
    """Controller handling Google Meet authentication for Odoo users."""
    @http.route('/google_meet_authentication', type="http", auth="user")
    def get_auth_code(self, **kw):
        """Retrieve the authentication code for Google Meet.

        Runs as the logged-in user without sudo, so only users allowed to
        edit the company's Google Meet settings can store new tokens.
        """
        company_id = request.env.company
        if kw.get('code'):
            # Accept only the answer to the request started from this
            # company's Authenticate button, and only once.
            expected_state = company_id.hangout_oauth_state
            if not expected_state or not hmac.compare_digest(
                    expected_state, kw.get('state') or ''):
                raise UserError(request.env._(
                    'Invalid or expired authentication request. Please '
                    'click Authenticate on the company form again.'))
            company_id.write({
                'hangout_company_authorization_code': kw.get('code'),
                'hangout_oauth_state': False,
            })
            client_id = company_id.hangout_client_id
            client_secret = company_id.hangout_client_secret
            redirect_uri = company_id.hangout_redirect_uri
            data = {
                'code': kw.get('code'),
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            response = requests.post(
                'https://accounts.google.com/o/oauth2/token', data=data,
                headers={
                    'content-type': 'application/x-www-form-urlencoded'},
                timeout=TIMEOUT)
            if response.json() and response.json().get('access_token'):
                company_id.write({
                    'hangout_company_access_token':
                        response.json().get('access_token'),
                    'hangout_company_access_token_expiry':
                        datetime.datetime.now() + datetime.timedelta(
                            seconds=response.json().get('expires_in')),
                    'hangout_company_refresh_token':
                        response.json().get('refresh_token'),
                })
                return request.make_response(
                    "Authentication successful. You can close this window.")
            raise UserError(
                request.env._('Something went wrong during the token '
                              'generation. Maybe your Authorization Code is '
                              'invalid.'))
        return request.make_response("")
