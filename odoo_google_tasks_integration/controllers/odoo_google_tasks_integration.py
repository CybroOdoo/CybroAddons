# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Jabin MP (odoo@cybrosys.com)
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
#############################################################################
import datetime
import requests
from odoo import http, _
from odoo.exceptions import UserError


class GoogleTaskAuth(http.Controller):
    """Controller for Google Task Authentication"""
    @http.route('/google_task_authentication', type="http", auth="public",
                website=True)
    def get_auth_code(self, **kw):
        """Get the authentication code from Google and save access tokens"""
        project_cred = http.request.env.ref(
            'odoo_google_tasks_integration.project_google_credential_data')
        if kw.get('code'):
            project_cred.write(
                {'hangout_company_authorization_code': kw.get('code')})
            data = {
                'code': kw.get('code'),
                'client_id':project_cred.hangout_client,
                'client_secret': project_cred.hangout_client_secret,
                'redirect_uri': project_cred.hangout_redirect_uri,
                'grant_type': 'authorization_code'
            }
            response = requests.post(
                'https://accounts.google.com/o/oauth2/token',
                data=data,
                headers={'content-type': 'application/x-www-form-urlencoded'})
            if response.json() and response.json().get('access_token'):
                project_cred.write({
                    'hangout_company_access_token': response.json().get(
                        'access_token'),
                    'hangout_company_access_token_expiry':
                        datetime.datetime.now() + datetime.timedelta(
                            seconds=response.json().get('expires_in')),
                    'hangout_company_refresh_token': response.json().get(
                        'access_token'),
                })
                return "Authentication Success. You can close this window."
            else:
                raise UserError(
                    _('Something went wrong during the token generation.'
                      'Maybe your Authorization Code is invalid')
                )
