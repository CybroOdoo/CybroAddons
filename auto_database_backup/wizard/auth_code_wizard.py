# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api, _

from werkzeug import urls

GOOGLE_AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_ENDPOINT = 'https://accounts.google.com/o/oauth2/token'


class AuthenticationWizard(models.TransientModel):
    _name = 'authentication.wizard'
    _description = 'Authentication Code Wizard'

    dropbox_authorization_code = fields.Char(string='Dropbox Authorization Code')
    dropbox_auth_url = fields.Char(string='Dropbox Authentication URL', compute='_compute_dropbox_auth_url')

    @api.depends('dropbox_authorization_code')
    def _compute_dropbox_auth_url(self):
        backup_config = self.env['db.backup.configure'].browse(self.env.context.get('active_id'))
        dropbox_auth_url = backup_config.get_dropbox_auth_url()
        for rec in self:
            rec.dropbox_auth_url = dropbox_auth_url

    def action_setup_dropbox_token(self):
        backup_config = self.env['db.backup.configure'].browse(self.env.context.get('active_id'))
        backup_config.set_dropbox_refresh_token(self.dropbox_authorization_code)

