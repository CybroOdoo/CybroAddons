# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#   You can modify it under the terms of the GNU LESSER
#   GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#   You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#   (LGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import json

import requests
from werkzeug import urls

from odoo import fields, models, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    """
    This model represents the configuration settings for the OneDrive
    integration in Odoo.It allows users to configure various parameters for
    OneDrive integration, including client ID, client secret, access token,
    and folder Name.
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
    onedrive_tenant_id = fields.Char(
        string="Onedrive Tenant Id",
        config_parameter='onedrive_integration_odoo.tenant_id',
        help="Director (tenant) id for accessing OneDrive API")
    onedrive_access_token = fields.Char(
        string='Onedrive Access Token',
        help="Access Token for authenticating with OneDrive API")
    onedrive_refresh_token = fields.Char(
        string='Onedrive Refresh Token',
        help="Refresh Token for refreshing the access token")
    onedrive_folder = fields.Char(
        string='Folder Name', help="Name of the folder in OneDrive",
        config_parameter='onedrive_integration_odoo.onedrive_folder')
    is_onedrive_enabled = fields.Boolean(
        string="Synchronize Onedrive with odoo",
        config_parameter='onedrive_integration_odoo.onedrive_button',
        help="Enable/Disable OneDrive integration")

    def action_get_onedrive_auth_code(self):
        """
        Generate onedrive authorization code
        """
        ir_config = self.env['ir.config_parameter'].sudo()
        client_id = self.onedrive_client or ir_config.get_str(
            'onedrive_integration_odoo.client_id', '')
        client_secret = self.onedrive_client_secret or ir_config.get_str(
            'onedrive_integration_odoo.client_secret', '')
        tenant_id = self.onedrive_tenant_id or ir_config.get_str(
            'onedrive_integration_odoo.tenant_id', '')
        base_url = ir_config.get_str('web.base.url', '')

        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
            'scope': "https://graph.microsoft.com/.default",
            'redirect_uri': base_url + '/onedrive/authentication'
        }
        res = requests.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data=data,
            headers={"content-type": "application/x-www-form-urlencoded"},
            timeout=10)
        response = res.content and res.json() or {}
        # If client_credentials returns invalid_client, secret or ID is wrong
        if response.get('error') == 'invalid_client':
            raise UserError(_("Error '%s': Please check your Client ID and Client Secret.",
                              response.get('error_description', response['error'])))
        else:
            authority = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
            action = self.env["ir.actions.client"].sudo()._for_xml_id(
                "onedrive_integration_odoo.onedrive_dashboard_action")
            record_id = self.id or 0
            url_return = f"{base_url}/web#id={record_id}&action={action['id']}&model=onedrive.dashboard"
            encoded_params = urls.url_encode({
                'response_type': 'code',
                'client_id': client_id,
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
