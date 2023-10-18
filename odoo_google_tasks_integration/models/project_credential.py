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
import requests
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

TIMEOUT = 20


class ProjectCredential(models.Model):
    """Model for Project Credentials for sync Google Tasks"""
    _name = "project.credential"
    _description = "Google Task Credentials"

    hangout_client = fields.Char(string="Client ID",
                                 help='Google Developer Console Client ID')
    hangout_client_secret = fields.Char(string="Client Secret",
                                        help='Google Developer Console '
                                             'Client Secret')
    hangout_redirect_uri = fields.Char(string="Authorized redirect URIs",
                                       default=request.httprequest.host_url,
                                       help='Google Authorized redirect URIs')
    hangout_company_access_token = fields.Char(string='Access Token',
                                               copy=False,
                                               help='Access token for Google'
                                                    ' Tasks API')
    hangout_company_access_token_expiry = fields.Datetime(
        string='Token expiry',
        help='Expiry date and time of the access token')
    hangout_company_refresh_token = fields.Char(string='Refresh Token',
                                                copy=False,
                                                help='Refresh token for Google'
                                                     'Tasks API')
    hangout_company_authorization_code = fields.Char(
        string="Authorization Code",
        help='Authorization code for authentication')
    hangout_company_api_key = fields.Char(string="Enter API Key",
                                          help='API key for Google Tasks API')
    name = fields.Char(string="Name", default="Credentials",
                       help='Name of the credentials')

    def action_google_task_company_authenticate(self):
        """Authenticate the company with Google Tasks API"""
        if not self.hangout_client:
            raise ValidationError("Please Enter Client ID")
        client_id = self.hangout_client
        if not self.hangout_redirect_uri:
            raise ValidationError("Please Enter Client Secret")
        redirect_url = self.hangout_redirect_uri
        calendar_scope = 'https://www.googleapis.com/auth/calendar'
        google_task_scope = 'https://www.googleapis.com/auth/tasks'
        url = (
            "https://accounts.google.com/o/oauth2/v2/auth?response_type=code"
            "&access_type=offline&client_id={}&redirect_uri={}&scope={}+{}"
        ).format(client_id, redirect_url, calendar_scope, google_task_scope)
        return {
            "type": 'ir.actions.act_url',
            "url": url,
            "target": "new"
        }

    def action_google_task_company_refresh_token(self):
        """Refresh the access token for Google Tasks API"""
        if not self.hangout_client:
            raise UserError(_('Client ID is not yet configured.'))
        client_id = self.hangout_client
        if not self.hangout_client_secret:
            raise UserError(_('Client Secret is not yet configured.'))
        client_secret = self.hangout_client_secret
        if not self.hangout_company_refresh_token:
            raise UserError(_('Refresh Token is not yet configured.'))
        refresh_token = self.hangout_company_refresh_token
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }
        response = requests.post(
            'https://accounts.google.com/o/oauth2/token',
            data=data,
            headers={'content-type': 'application/x-www-form-urlencoded'},
            timeout=TIMEOUT)
        if response.json() and response.json().get('access_token'):
            self.write({
                'hangout_company_access_token': response.json().get(
                    'access_token'),
            })
        else:
            raise UserError(
                _('Something went wrong during the token generation. '
                  'Please request again an authorization code.'))
