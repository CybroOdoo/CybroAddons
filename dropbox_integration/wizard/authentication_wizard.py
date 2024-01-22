# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Subina P (odoo@cybrosys.com)
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
from odoo import models, fields, api


class AuthenticationWizard(models.TransientModel):
    """
    Generates auth code
    """
    _name = 'authentication.wizard'
    _description = 'Authentication Code Wizard'

    dropbox_authorization_code = fields.Char(
        string='Dropbox Authorization Code', help='Dropbox Authorization Code')
    dropbox_auth_url = fields.Char(string='Dropbox Authentication URL',
                                   compute='_compute_dropbox_auth_url',
                                   help='Dropbox Authentication URL')

    @api.depends('dropbox_authorization_code')
    def _compute_dropbox_auth_url(self):
        """        Compute method to update the Dropbox Authentication URL
        based on the provided authorization code.
        """
        dbx_config = self.env['res.config.settings'].browse(
            self.env.context.get('active_id'))
        for rec in self:
            rec.dropbox_auth_url = dbx_config.get_dropbox_auth_url()

    def action_setup_dropbox_token(self):
        """        Action method to set up the Dropbox refresh token using the
        provided authorization code.
        """
        dbx_config = self.env['res.config.settings'].browse(
            self.env.context.get('active_id'))
        dbx_config.set_dropbox_refresh_token(
            self.dropbox_authorization_code)
