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
import requests
from odoo import exceptions, fields, models, _


class UploadFile(models.TransientModel):
    """ Model for opening the file upload wizard view."""

    _name = "upload.file"
    _description = "Upload File"

    file = fields.Binary(string="Attachment", help="Select a file to upload")
    file_name = fields.Char(string="File Name",
                            help="Name of the file to upload")

    def action_upload_file(self):
        """Upload file to OneDrive."""
        if not self.file:
            raise exceptions.UserError(_('Please attach a file to upload.'))
        # Searching for attachments related to the current upload.file record
        attachment = self.env["ir.attachment"].search(
            ['|', ('res_field', '!=', False), ('res_field', '=', False),
             ('res_id', '=', self.id),
             ('res_model', '=', 'upload.file')])
        # Getting the access token and folder ID from the onedrive.dashboard
        # and ir.config_parameter models
        token = self.env['onedrive.dashboard'].search([], order='id desc',
                                                      limit=1)
        folder = self.env['ir.config_parameter'].get_param(
            'onedrive_integration_odoo.folder_id', '')
        if not token or not folder:
            raise exceptions.UserError(
                _('Please set up Access Token and Folder ID.'))
        # Refreshing the token if it has expired
        if token.token_expiry_date <= str(fields.Datetime.now()):
            token.generate_onedrive_refresh_token()
        try:
            # Creating an upload session for the file
            url = "http://graph.microsoft.com/v1.0/me/drive/items/%s:/%s:/" \
                  "createUploadSession" % (folder, self.file_name)
            upload_session = requests.post(url, headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer "' + token.onedrive_access_token + '"'
            })
            upload_url = upload_session.json().get('uploadUrl')
            # Uploading the file to the upload session URL
            requests.put(upload_url, data=open(
                (attachment._full_path(attachment.store_fname)), 'rb'))
            # Returning a success notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _(
                        'File has been uploaded successfully. Please refresh.'),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        except Exception as error:
            # Returning a warning notification if the upload fails
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': _('Failed to upload: %s' % error),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
