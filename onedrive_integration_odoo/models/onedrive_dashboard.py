# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Aslam A K( odoo@cybrosys.com )
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import json
import logging
import requests
from datetime import timedelta
from odoo import fields, models, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class OneDriveDashboard(models.Model):
    """Model for generating refresh and access tokens for OneDrive."""

    _name = 'onedrive.dashboard'
    _description = "OneDrive Dashboard"

    onedrive_access_token = fields.Char(string="OneDrive Access Token",
                                        store=True,
                                        help="Access token for OneDrive API "
                                             "authentication")
    onedrive_refresh_token = fields.Char(string="OneDrive Refresh Token",
                                         help="Refresh token for obtaining "
                                              "new access tokens")
    token_expiry_date = fields.Char(string="OneDrive Token Validity",
                                    help="Validity or expiration status of the"
                                         " OneDrive access token")
    upload_file = fields.Binary(string="Upload File",
                                help="Binary data of the file to be uploaded "
                                     "to OneDrive")

    def get_tokens(self, authorize_code):
        """Generate OneDrive tokens from authorization code."""
        data = {
            'code': authorize_code,
            'client_id': self.env['ir.config_parameter'].get_param(
                'onedrive_integration_odoo.client_id', ''),
            'client_secret': self.env['ir.config_parameter'].get_param(
                'onedrive_integration_odoo.client_secret', ''),
            'grant_type': 'authorization_code',
            'scope': ['offline_access openid Files.ReadWrite.All'],
            'redirect_uri': request.env['ir.config_parameter'].get_param(
                'web.base.url') + '/onedrive/authentication'
        }
        try:
            res = requests.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data=data,
                headers={"content-type": "application/x-www-form-urlencoded"}
            )
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.env['onedrive.dashboard'].create({
                    'onedrive_access_token': response.get('access_token'),
                    'onedrive_refresh_token': response.get('refresh_token'),
                    'token_expiry_date': fields.Datetime.now() + timedelta(
                        seconds=expires_in) if expires_in else False,
                })
        except requests.HTTPError as error:
            _logger.exception(_("Bad Microsoft OneDrive request: %s !"),
                              error.response.content)
            raise error

    def generate_onedrive_refresh_token(self):
        """Generate OneDrive access token from refresh token if expired."""
        data = {
            'client_id': self.env['ir.config_parameter'].get_param(
                'onedrive_integration_odoo.client_id', ''),
            'client_secret': self.env['ir.config_parameter'].get_param(
                'onedrive_integration_odoo.client_secret', ''),
            'scope': ['offline_access openid Files.ReadWrite.All'],
            'grant_type': "refresh_token",
            'redirect_uri': request.env['ir.config_parameter'].get_param(
                'web.base.url') + '/onedrive/authentication',
            'refresh_token': self.onedrive_refresh_token
        }
        try:
            res = requests.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data=data,
                headers={"Content-type": "application/x-www-form-urlencoded"}
            )
            res.raise_for_status()
            response = res.content and res.json() or {}
            if response:
                expires_in = response.get('expires_in')
                self.write({
                    'onedrive_access_token': response.get('access_token'),
                    'onedrive_refresh_token': response.get('refresh_token'),
                    'token_expiry_date': fields.Datetime.now() + timedelta(
                        seconds=expires_in) if expires_in else False,
                })
        except requests.HTTPError as error:
            _logger.exception(_("Bad Microsoft OneDrive request: %s !"),
                              error.response.content)
            raise error

    def action_synchronize_onedrive(self):
        """Pass the files to JavaScript."""
        record = self.search([], order='id desc', limit=1)
        if not record:
            return False
        if record.token_expiry_date <= str(fields.Datetime.now()):
            record.generate_onedrive_refresh_token()
        folder = self.env['ir.config_parameter'].get_param(
            'onedrive_integration_odoo.folder_id', '')
        if not folder:
            return False
        url = "https://graph.microsoft.com/v1.0/me/drive/items/%s/children?Content-Type=application/json" % folder
        response = requests.request("GET", url, headers={
            'Authorization': 'Bearer "' + record.onedrive_access_token + '"'},
                                    data={})
        message = json.loads(response.content)
        if 'error' in message:
            return ['error', message['error']['code'],
                    message['error']['message']]
        files = {}
        for file in response.json().get('value'):
            if list(file.keys())[0] == '@microsoft.graph.downloadUrl':
                files[file['name']] = file['@microsoft.graph.downloadUrl']
        return files
