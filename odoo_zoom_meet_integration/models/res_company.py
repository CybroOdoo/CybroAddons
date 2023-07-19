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
import requests
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError

TIMEOUT = 20


class ResCompany(models.Model):
    """Inheriting company model for configuring zoom odoo connector"""
    _inherit = "res.company"

    zoom_client = fields.Char(
        string="Client Id", help='Zoom Developer Console Client ID')
    zoom_client_secret = fields.Char(
        string="Client Secret", help='Zoom Developer Console Client Secret')
    zoom_redirect_uri = fields.Char(
        string="Authorized redirect URIs", default="http://localhost:8015"
                                                   "/zoom_meet_authentication",
        help='Zoom Authorized redirect URIs')
    zoom_company_access_token = fields.Char(string='Access Token',
                                            copy=False,
                                            help='Access token for '
                                                 'respective company')
    zoom_company_access_token_expiry = fields.Datetime(
        string='Token expiry', help='Access token expiration')
    zoom_company_refresh_token = fields.Char(string='Refresh Token',
                                             copy=False,
                                             help='Refresh token for '
                                                  'respective company')
    zoom_company_authorization_code = fields.Char(string="Authorization Code",
                                                  help='Authorization Code '
                                                       'for respective company')

    def action_zoom_meet_company_authenticate(self):
        """Authentication for zoom"""
        if not self.zoom_client:
            raise ValidationError("Please Enter Client ID")
        client_id = self.zoom_client
        if not self.zoom_redirect_uri:
            raise ValidationError("Please Enter Client Secret")
        redirect_url = self.zoom_redirect_uri
        url = (
            "https://zoom.us/oauth/authorize?response_type=code"
            "&client_id={}&redirect_uri={}"
        ).format(client_id, redirect_url)
        return {
            "type": 'ir.actions.act_url',
            "url": url,
            "target": "current"
        }

    def action_zoom_meet_company_refresh_token(self):
        """Generate refresh token"""
        if not self.zoom_client:
            raise UserError(
                _('Client ID is not yet configured.'))
        client_id = self.zoom_client
        if not self.zoom_client_secret:
            raise UserError(
                _('Client Secret is not yet configured.'))
        client_secret = self.zoom_client_secret
        if not self.zoom_company_refresh_token:
            raise UserError(
                _('Refresh Token is not yet configured.'))
        refresh_token = self.zoom_company_refresh_token
        data = {
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }
        b64 = str(
            client_id + ":" + client_secret).encode(
            'utf-8')
        b64 = base64.b64encode(b64).decode('utf-8')
        response = requests.post(
            'https://zoom.us/oauth/token', data=data,
            headers={
                'Authorization': 'Basic ' + b64,
                'content-type': 'application/x-www-form-urlencoded'},
            timeout=TIMEOUT)
        if response.json() and response.json().get('access_token'):
            self.write({
                'zoom_company_access_token':
                    response.json().get('access_token'),
            })
        else:
            raise UserError(
                _('Something went wrong during the token generation.'
                  ' Please request again an authorization code.'))
