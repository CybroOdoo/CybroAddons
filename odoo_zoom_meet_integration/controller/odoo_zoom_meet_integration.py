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
import base64
import datetime
import requests
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError


class ZoomMeetAuth(http.Controller):
    """ This controller is responsible for the Authentication of
    connection from Odoo to Zoom"""

    @http.route('/zoom_meet_authentication', type="http", auth="public",
                website=True)
    def get_auth_code(self, **kw):
        """Authentication for connecting Odoo to Zoom"""
        user_id = request.uid
        company_id = http.request.env['res.users'].sudo().browse(
            user_id).company_id
        if kw.get('code'):
            company_id.write(
                {'zoom_company_authorization_code': kw.get('code')})
            client_id = company_id.zoom_client
            client_secret = company_id.zoom_client_secret
            redirect_uri = company_id.zoom_redirect_uri
            data = {
                'code': kw.get('code'),
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            b64 = str(
                client_id + ":" + client_secret).encode(
                'utf-8')
            b64 = base64.b64encode(b64).decode('utf-8')
            response = requests.post(
                'https://zoom.us/oauth/token', data=data,
                headers={
                    'Authorization': 'Basic ' + b64,
                    'content-type': 'application/x-www-form-urlencoded'})
            if response.json() and response.json().get('access_token'):
                company_id.write({
                    'zoom_company_access_token':
                        response.json().get('access_token'),
                    'zoom_company_access_token_expiry':
                        datetime.datetime.now() + datetime.timedelta(
                            seconds=response.json().get('expires_in')),
                    'zoom_company_refresh_token':
                        response.json().get('refresh_token'),
                })
                return "Authentication Success. You Can Close this window"
            else:
                raise UserError(
                    _('Something went wrong during the token generation.'
                      'Maybe your Authorization Code is invalid'))
