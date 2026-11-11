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
import base64
import requests
from odoo import fields, models, _
from odoo.exceptions import UserError


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
        self.ensure_one()
        if not self.file:
            raise UserError(_('Please Attach a file to upload.'))
        token = self.env['onedrive.dashboard'].search([], order='id desc',
                                                      limit=1)
        if hasattr(self.file, 'content'):
            file_content = self.file.content
        elif isinstance(self.file, str):
            try:
                file_content = base64.b64decode(self.file)
            except Exception:
                file_content = self.file.encode('utf-8')
        elif isinstance(self.file, bytes):
            file_content = self.file
        else:
            attachment = self.env["ir.attachment"].search(
                [('res_id', '=', self.id), ('res_model', '=', 'upload.file')],
                limit=1)
            raw = attachment.raw if attachment else b''
            file_content = raw.content if hasattr(raw, 'content') else raw
        folder = self.env['ir.config_parameter'].sudo().get_str(
            'onedrive_integration_odoo.onedrive_folder', '')
        if not token or not folder:
            raise UserError(
                _('Please setup Access Token and Folder Name.'))
        if not token.token_expiry_date or token.token_expiry_date <= fields.Datetime.now():
            token.generate_onedrive_refresh_token()

        url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{folder}/{self.file_name}:/content"
        headers = {
            'Authorization': f'Bearer {token.onedrive_access_token}',
            'Content-Type': 'application/octet-stream'
        }
        try:
            response = requests.put(url, headers=headers, data=file_content, timeout=10)
            if response.status_code in [200, 201]:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'success',
                        'message': _('File uploaded successfully to OneDrive. Please refresh'),
                    }
                }
            raise UserError(
                _("Upload failed: %(status)s - %(text)s",
                  status=response.status_code, text=response.text)
            )
        except requests.RequestException as e:
            raise UserError(_("Network error: %s", str(e)))
