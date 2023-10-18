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


class DropboxUpload(models.TransientModel):
    """
    Model to upload files to Dropbox
    """
    _name = "dropbox.upload"
    _description = "Dropbox Upload"

    file = fields.Binary(string="Attachment", help="Select a file to upload")
    file_name = fields.Char(string="File Name",
                            help="Name of the uploaded file")

    def action_upload_file(self):
        """
        Function to upload attachments to dropbox
        """
        try:
            access = self.env['dropbox.dashboard'].search([], order='id desc',
                                                          limit=1)
            dbx = dropbox.Dropbox(app_key=access.dropbox_client,
                                  app_secret=access.dropbox_client_secret,
                                  oauth2_refresh_token=access.dropbox_refresh_token)
            attachment = self.env["ir.attachment"].search(
                ['|', ('res_field', '!=', False), ('res_field', '=', False),
                 ('res_id', '=', self.id),
                 ('res_model', '=', 'dropbox.upload')])
            path = self.env['ir.config_parameter'].get_param(
                'dropbox_integration.folder_id')
            dropbox_destination = path + '/' + self.file_name
            file = open(attachment._full_path(attachment.store_fname), 'rb')
            dbx.files_upload(file.read(), dropbox_destination)
            file.close()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': 'File uploaded successfully. '
                               'Please refresh the page.',
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        except Exception as error:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': 'Failed to upload: %s' % error,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
