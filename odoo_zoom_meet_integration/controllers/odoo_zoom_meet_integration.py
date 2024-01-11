# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
################################################################################
import base64
import datetime
import requests
from odoo import fields, http, _
from odoo.http import request
from odoo.exceptions import ValidationError


class ZoomMeetAuth(http.Controller):
    """ This controller is responsible for the authentication of
    connection from Odoo to Zoom"""

    @http.route('/zoom_meet_authentication', type="http", auth="public",
                website=True)
    def get_auth_code(self, **kw):
        """Authentication for connecting Odoo with Zoom"""
        company_id = http.request.env['res.users'].sudo().browse(
            request.uid).company_id
        if kw.get('code'):
            company_id.write(
                {'zoom_company_authorization_code': kw.get('code')})
            data = {
                'code': kw.get('code'),
                'redirect_uri': company_id.zoom_redirect_uri,
                'grant_type': 'authorization_code'
            }
            response = requests.post(
                'https://zoom.us/oauth/token', data=data,
                headers={
                    'Authorization': 'Basic ' + base64.b64encode(str(
                        company_id.zoom_client + ":" +
                company_id.zoom_client_secret).encode('utf-8')).decode('utf-8'),
                    'content-type': 'application/x-www-form-urlencoded'})
            if response.json() and response.json().get('access_token'):
                company_id.write({
                    'zoom_company_access_token':
                        response.json().get('access_token'),
                    'zoom_company_access_token_expiry':
                        fields.Datetime.now() + datetime.timedelta(
                            seconds=response.json().get('expires_in')),
                    'zoom_company_refresh_token':
                        response.json().get('refresh_token'),
                })
                return "Authentication Success. You can close this Window"
            else:
                raise ValidationError(
                    _('Something went wrong during the token generation.'
                      'Your Authorization Code may be invalid'))
