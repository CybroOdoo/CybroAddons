# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina (odoo@cybrosys.com)
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
import requests
import datetime
from odoo import http
from odoo import _
from odoo.exceptions import UserError
from odoo.http import request


class GoogleMeetAuth(http.Controller):
    """Controller handling Google Meet authentication for Odoo users."""
    @http.route('/google_meet_authentication', type="http", auth="public",
                website=True)
    def get_auth_code(self, **kw):
        """  Retrieve the authentication code for Google Meet."""
        user_id = request.uid
        company_id = http.request.env['res.users'].sudo().search(
            [('id', '=', user_id)], limit=1).company_id
        if kw.get('code'):
            company_id.write(
                {'hangout_company_authorization_code': kw.get('code')})
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
                    'content-type': 'application/x-www-form-urlencoded'})
            if response.json() and response.json().get('access_token'):
                company_id.write({
                    'hangout_company_access_token':
                        response.json().get('access_token'),
                    'hangout_company_access_token_expiry':
                        datetime.datetime.now() + datetime.timedelta(
                            seconds=response.json().get('expires_in')),
                    'hangout_company_refresh_token':
                        response.json().get('access_token'),
                })
                return "Authentication Success. You Can Close this window"
            else:
                raise UserError(
                    _('Something went wrong during the token generation.'
                      'Maybe your Authorization Code is invalid')
                )
