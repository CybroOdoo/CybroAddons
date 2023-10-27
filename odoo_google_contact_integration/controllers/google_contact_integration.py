# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import datetime
import requests
from odoo import _
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError

TIMEOUT = 20


class GoogleContactAuth(http.Controller):
    """Controller for Google Contact authentication. """
    @http.route('/google_contact_authentication', type="http", auth="public",
                website=True)
    def get_auth_code(self, **kw):
        """Connect your Google account with the OAuth Authentication process.
           You will be redirected to the Google login page
           where you will need to accept the permission."""
        user_id = request.uid
        company_id = http.request.env['res.users'].sudo().search(
            [('id', '=', user_id)], limit=1).company_id
        if kw.get('code'):
            company_id.write(
                {'contact_company_authorization_code': kw.get('code')})
            data = {
                'code': kw.get('code'),
                'client_id': company_id.contact_client_id,
                'client_secret': company_id.contact_client_secret,
                'redirect_uri': company_id.contact_redirect_uri,
                'grant_type': 'authorization_code'
            }
            response = requests.post(
                'https://accounts.google.com/o/oauth2/token', data=data,
                headers={
                    'content-type': 'application/x-www-form-urlencoded'},
                timeout=TIMEOUT)
            if response.json() and response.json().get('access_token'):
                company_id.write({
                    'contact_company_access_token':
                        response.json().get('access_token'),
                    'contact_company_access_token_expiry':
                        datetime.datetime.now() + datetime.timedelta(
                            seconds=response.json().get('expires_in')),
                    'contact_company_refresh_token':
                        response.json().get('access_token'),
                })
                return "Authentication Success. You Can Close this window"
            else:
                raise UserError(
                    _('Something went wrong during the token generation.'
                      'Maybe your Authorization Code is invalid')
                )
