# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Akhil ( odoo@cybrosys.com )
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
import base64
import requests
from odoo.exceptions import UserError
from odoo import exceptions, fields, models, _


class UploadFile(models.TransientModel):
    """
    For opening wizard view
    """
    _name = "upload.file"
    _description = "Upload File"

    file = fields.Binary(string="Attachment", help="Select a file to upload")
    file_name = fields.Char(string="File Name", help="Name of the attachment")

    def action_upload_file(self):
        """
        Upload file to onedrive
        """
        if not self.file:
            raise exceptions.UserError(_('Please Attach a file to upload.'))
        attachment = self.env["ir.attachment"].search(
            ['|', ('res_field', '!=', False), ('res_field', '=', False),
             ('res_id', '=', self.id),
             ('res_model', '=', 'upload.file')])
        token = self.env['onedrive.dashboard'].search([], order='id desc',
                                                      limit=1)
        file_content = base64.b64decode(attachment.datas)
        folder = self.env['ir.config_parameter'].get_param(
            'onedrive_integration_odoo.onedrive_folder', '')
        if not token or not folder:
            raise exceptions.UserError(
                _('Please setup Access Token and Folder Name.'))
        if token.token_expiry_date <= str(fields.Datetime.now()):
            token.generate_onedrive_refresh_token()

        url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{folder}/{self.file_name}:/content"
        headers = {
                'Authorization': f'Bearer {token.onedrive_access_token }',
                'Content-Type': 'application/octet-stream'
            }
        try:
            response = requests.put(url, headers=headers, data=file_content)
            if response.status_code in [200, 201]:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'success',
                        'message': 'File uploaded successfully to OneDrive.'
                                   'Please refresh',
                    }
                }
            else:
                raise UserError(
                    _("Upload failed: %s - %s") %
                    (response.status_code, response.text)
                )
        except requests.RequestException as e:
            raise UserError(_("Network error: %s") % str(e))
