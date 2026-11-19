# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
import dropbox

from odoo import fields, models
from odoo.exceptions import AccessError, ValidationError


class ResConfigSettings(models.TransientModel):
    """ Generate and manage Dropbox refresh token and settings. """
    _inherit = 'res.config.settings'

    dropbox_client_id = fields.Char(
        string='Dropbox Client ID', copy=False,
        config_parameter='dropbox_integration.client_id',
        help="Dropbox Client ID")
    dropbox_client_secret = fields.Char(
        string='Dropbox Client Secret', copy=False,
        config_parameter='dropbox_integration.client_secret',
        help="Dropbox Client Secret")
    dropbox_folder_id = fields.Char(
        string='Folder ID', config_parameter='dropbox_integration.folder_id',
        help="Dropbox Folder ID")
    dropbox_button = fields.Boolean(
        string='Dropbox',
        config_parameter='dropbox_integration.dropbox_button',
        default=False, help="Enable Dropbox integration")

    def action_get_dropbox_auth_code(self):
        """ Open a wizard to set up the Dropbox authorization code. """
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(self.env._("Access Denied: Only administrators can configure Dropbox integration."))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dropbox Authorization Wizard',
            'res_model': 'dropbox.authentication',
            'view_mode': 'form',
            'target': 'new',
            'context': {'dropbox_auth': True}
        }

    def get_dropbox_auth_url(self):
        """ Return Dropbox authorization URL. """
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(self.env._("Access Denied: Only administrators can access Dropbox authentication URL."))
        params = self.env['ir.config_parameter'].sudo()
        client_id = (self.dropbox_client_id if self else False) or params.get_str('dropbox_integration.client_id')
        client_secret = (self.dropbox_client_secret if self else False) or params.get_str('dropbox_integration.client_secret')
        if not client_id or not client_secret:
            raise ValidationError(
                self.env._("Please configure Client ID and Client Secret in Settings first.")
            )
        dbx_auth = dropbox.oauth.DropboxOAuth2FlowNoRedirect(
            client_id, client_secret,
            token_access_type='offline')
        return dbx_auth.start()

    def set_dropbox_refresh_token(self, auth_code):
        """ Generate and set the Dropbox refresh token from the authorization code. """
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(self.env._("Access Denied: Only administrators can configure Dropbox integration."))
        try:
            params = self.env['ir.config_parameter'].sudo()
            client_id = (self.dropbox_client_id if self else False) or params.get_str('dropbox_integration.client_id')
            client_secret = (self.dropbox_client_secret if self else False) or params.get_str('dropbox_integration.client_secret')
            dbx_auth = dropbox.oauth.DropboxOAuth2FlowNoRedirect(
                client_id, client_secret,
                token_access_type='offline')
            oauth_result = dbx_auth.finish(auth_code)
            dashboard = self.env['dropbox.dashboard'].sudo().search(
                [], order='id desc', limit=1)
            vals = {
                'dropbox_client_id': client_id,
                'dropbox_client_secret': client_secret,
                'dropbox_refresh_token': oauth_result.refresh_token,
            }
            if dashboard:
                dashboard.write(vals)
            else:
                self.env['dropbox.dashboard'].sudo().create(vals)
        except Exception as e:
            raise ValidationError(
                self.env._("Failed to connect with Dropbox (%s).", e)
            ) from e
