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
from werkzeug import urls
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    onedrive_client = fields.Char(
        string='Onedrive Client ID',
        copy=False,
        config_parameter='onedrive_integration_odoo.client_id',
        help='The Onedrive client ID from the Developer credentials.')
    onedrive_client_secret = fields.Char(
        string='Onedrive Client Secret',
        config_parameter='onedrive_integration_odoo.client_secret',
        help='The Onedrive client secret from Developer credentials.')
    onedrive_access_token = fields.Char(
        string='Onedrive Access Token',
        help='Access token generated from onedrive')
    onedrive_tenant_id = fields.Char(
        string="Onedrive Tenant Id",
        config_parameter='onedrive_integration_odoo.tenant_id',
        help="Director (tenant) id for accessing OneDrive API")
    onedrive_refresh_token = fields.Char(
        string='Onedrive Refresh Token',
        help='Refresh token generated from onedrive')
    token_expiry_date = fields.Datetime(
        string='Onedrive Token Validity',
        help='Access token expiry date')
    onedrive_folder = fields.Char(
        string='Folder ID',
        config_parameter='onedrive_integration_odoo.folder_id',
        help='Onedrive Folder Id from url')
    is_onedrive_integration = fields.Boolean(
        string='Onedrive Cloud Storage',
        config_parameter='onedrive_integration_odoo.onedrive_button',
        default=False,
        help="Login to Microsoft to get access token")

    def action_get_onedrive_auth_code(self):
        """ Generate Onedrive authorization code """
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
        tenant_id = self.env['ir.config_parameter'].get_param(
            'onedrive_integration_odoo.tenant_id', '')
        res = requests.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data=data,
            headers={"content-type": "application/x-www-form-urlencoded"}
        )
        response = res.content and res.json() or {}
        if 'error' in response:
            _logger.warning(response)
            raise UserError(_("Error '%s': Please check the credentials.",
                              response['error']))
        else:
            authority = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
            action = self.env["ir.actions.client"].sudo()._for_xml_id(
                "onedrive_integration_odoo.onedrive_dashboard_action")
            base_url = request.env['ir.config_parameter'].get_param(
                'web.base.url')
            url_return = base_url + '/web#id=%d&action=%d&view_type=form&model=%s' % (
                self.id, action['id'], 'onedrive.dashboard')
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
