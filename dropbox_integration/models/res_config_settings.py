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
import dropbox
from odoo import fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """
    Generates the refresh token
    """
    _inherit = 'res.config.settings'

    dropbox_client_id = fields.Char(string='dropbox Client ID', copy=False,
                                    config_parameter=
                                    'dropbox_integration.client_id',
                                    help="Dropbox Client ID")
    dropbox_client_secret = fields.Char(string='dropbox Client Secret',
                                        copy=False,
                                        config_parameter=
                                        'dropbox_integration.client_secret',
                                        help="Dropbox Client Secret")
    dropbox_access_token = fields.Char(string='dropbox Access Token',
                                       help="Dropbox Access Token")
    dropbox_refresh_token = fields.Char(string='dropbox Refresh Token',
                                        help="Dropbox Refresh Token")
    dropbox_token_validity = fields.Datetime(string='dropbox Token Validity',
                                             help="Dropbox Token Validity")
    dropbox_folder_id = fields.Char(string='Folder ID',
                                    config_parameter=
                                    'dropbox_integration.folder_id',
                                    help="Dropbox Folder ID")
    dropbox_button = fields.Boolean(
        config_parameter='dropbox_integration.dropbox_button',
        default=False, help="Dropbox Button")

    def action_get_dropbox_auth_code(self):
        """
        Open a wizard to set up dropbox Authorization code
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dropbox Authorization Wizard',
            'res_model': 'authentication.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'dropbox_auth': True}
        }

    def get_dropbox_auth_url(self):
        """
        Return dropbox authorization url.
        """
        dbx_auth = dropbox.oauth.DropboxOAuth2FlowNoRedirect(
            self.env['ir.config_parameter'].get_param(
                'dropbox_integration.client_id'),
            self.env['ir.config_parameter'].get_param(
                'dropbox_integration.client_secret'),
            token_access_type='offline')
        return dbx_auth.start()

    def set_dropbox_refresh_token(self, auth_code):
        """
        Generate and set the dropbox refresh token from authorization code.
        """
        try:
            client_id = self.env['ir.config_parameter'].get_param(
                'dropbox_integration.client_id')
            client_secret = self.env['ir.config_parameter'].get_param(
                'dropbox_integration.client_secret')
            dbx_auth = dropbox.oauth.DropboxOAuth2FlowNoRedirect(
                client_id, client_secret,
                token_access_type='offline')
            outh_result = dbx_auth.finish(auth_code)
            self.env['dropbox.dashboard'].create({
                'dropbox_client_id': client_id,
                'dropbox_client_secret': client_secret,
                'dropbox_refresh_token': outh_result.refresh_token,
                'dropbox_access_token': outh_result.access_token,
            })
        except Exception as e:
            raise ValidationError(
                'Failed to Connect with Dropbox ( %s .)' % e)
