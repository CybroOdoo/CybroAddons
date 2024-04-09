# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Jumana Haseen ( odoo@cybrosys.com )
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
import requests
from werkzeug import urls
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.http import request


class ResConfigSettings(models.TransientModel):
    """
    This model represents the configuration settings for the OneDrive
    integration in Odoo.It allows users to configure various parameters for
    OneDrive integration, including client ID, client secret, access token,
    and folder ID.
    """
    _inherit = 'res.config.settings'

    onedrive_client = fields.Char(
        string='Onedrive Client ID', copy=False,
        config_parameter='onedrive_integration_odoo.client_id',
        help="Client ID for accessing OneDrive API")
    onedrive_client_secret = fields.Char(
        string='Onedrive Client Secret',
        config_parameter='onedrive_integration_odoo.client_secret',
        help="Client Secret for accessing OneDrive API")
    onedrive_access_token = fields.Char(
        string='Onedrive Access Token',
        help="Access Token for authenticating with OneDrive API")
    onedrive_refresh_token = fields.Char(
        string='Onedrive Refresh Token',
        help="Refresh Token for refreshing the access token")
    onedrive_folder = fields.Char(
        string='Folder ID', help="ID of the folder in OneDrive",
        config_parameter='onedrive_integration_odoo.folder_id')
    is_onedrive_enabled = fields.Boolean(
        string="Synchronize Onedrive with odoo",
        config_parameter='onedrive_integration_odoo.onedrive_button',
        help="Enable/Disable OneDrive integration")

    def action_get_onedrive_auth_code(self):
        """
        Generate onedrive authorization code
        """
        data = {
            'client_id': self.env['ir.config_parameter'].get_param(
                'onedrive_integration_odoo.client_id', ''),
            'client_secret': self.env['ir.config_parameter'].get_param(
                'onedrive_integration_odoo.client_secret', ''),
            'grant_type': 'client_credentials',
            'scope': "https://graph.microsoft.com/.default",
            'redirect_uri': request.env['ir.config_parameter'].get_param(
                'web.base.url') + '/onedrive/authentication'
        }
        res = requests.post(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            data=data,
            headers={"content-type": "application/x-www-form-urlencoded"})
        response = res.content and res.json() or {}
        if 'error' in response:
            raise UserError(_("Error '%s': Please check the credentials.",
                              response['error']))
        else:
            authority = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
            action = self.env["ir.actions.client"].sudo()._for_xml_id(
                "onedrive_integration_odoo.onedrive_dashboard_action")
            base_url = request.env['ir.config_parameter'].get_param(
                'web.base.url')
            url_return = base_url + '/web#id=%d&action=%d&view_type=form&model=%s' \
                         % (self.id, action['id'], 'onedrive.dashboard')
            encoded_params = urls.url_encode({
                'response_type': 'code',
                'client_id': self.env['ir.config_parameter'].get_param(
                    'onedrive_integration_odoo.client_id', ''),
                'state': json.dumps({
                    'onedrive_config_id': self.id,
                    'url_return': url_return
                }),
                'scope': ['offline_access openid Files.ReadWrite.All'],
                'redirect_uri': base_url + '/onedrive/authentication',
                'prompt': 'consent',
                'access_type': 'offline'
            })
            return {
                'type': 'ir.actions.act_url',
                'target': 'self',
                'url': "%s?%s" % (authority, encoded_params),
            }
