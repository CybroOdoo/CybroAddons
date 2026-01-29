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


class DropboxDashboard(models.Model):
    """ Dropbox dashboard model to connect with dropbox files."""
    _name = 'dropbox.dashboard'
    _description = 'Dropbox Dashboard'

    dropbox_client = fields.Char(string='Dropbox Client ID',
                                 help="Dropbox Client ID from dropbox api"
                                      " credentials")
    dropbox_client_secret = fields.Char(string='Dropbox Client Secret',
                                        help="Dropbox Client Secret from"
                                             " dropbox api credentials")
    dropbox_refresh_token = fields.Char(string='Dropbox Refresh Token',
                                        help="Dropbox Access Token generated "
                                             "by dropbox api credentials")
    dropbox_access_token = fields.Char(string='Dropbox Access Token',
                                       help="Dropbox Refresh Token generated "
                                            "by dropbox api credentials")
    dropbox_expire_date = fields.Datetime(string='Dropbox Expiry Date',
                                          help="Dropbox Access Token expiry"
                                               "date")

    def action_import_files(self):
        """ Import all files from dropbox folder """
        try:
            access = self.env['dropbox.dashboard'].search([], order='id desc',
                                                          limit=1)
            if not access:
                return False
            dbx = dropbox.Dropbox(app_key=access.dropbox_client,
                                  app_secret=access.dropbox_client_secret,
                                  oauth2_refresh_token=
                                  access.dropbox_refresh_token)
            path = self.env['ir.config_parameter'].get_param(
                'dropbox_integration.folder_id')
            response = dbx.files_list_folder(path=path)
            data = {}
            for files in response.entries:
                file = dbx.files_get_temporary_link(path=files.path_lower)
                data[file.metadata.name] = file.link
            return data
        except Exception as error:
            return ['error', error]
