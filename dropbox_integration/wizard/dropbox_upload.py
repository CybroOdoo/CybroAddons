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
import time

import dropbox
import requests

from odoo import fields, models
from odoo.exceptions import AccessError


class DropboxUpload(models.TransientModel):
    """ Wizard to upload files to Dropbox. """
    _name = "dropbox.upload"
    _description = "Dropbox Upload"

    file = fields.Binary("Attachment", help="Select a file to upload")
    file_name = fields.Char(string="File Name", help="Name of the file to upload")

    def action_upload_file(self):
        """ Upload files to Dropbox. """
        if not self.env.user.has_group('base.group_user'):
            raise AccessError(self.env._("Access Denied: Only internal users can upload files to Dropbox."))
        try:
            access = self.env['dropbox.dashboard'].sudo().search(
                [], order='id desc', limit=1)
            if not access or not access.dropbox_refresh_token:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'warning',
                        'message': self.env._(
                            'Failed to upload: Dropbox credentials not configured. '
                            'Please configure Dropbox in Settings.'
                        ),
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }

            dbx = dropbox.Dropbox(app_key=access.dropbox_client_id,
                                  app_secret=access.dropbox_client_secret,
                                  oauth2_refresh_token=access.dropbox_refresh_token)

            # Retrieve file data from binary field or attachment
            file_data = bytes(self.file) if self.file else b""
            if not file_data:
                attachment = self.env["ir.attachment"].search([
                    ('res_model', '=', 'dropbox.upload'),
                    ('res_id', '=', self.id),
                ], limit=1)
                if attachment:
                    file_data = bytes(attachment.raw) if attachment.raw else (
                        base64.b64decode(attachment.datas) if attachment.datas else b""
                    )

            if not file_data:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'warning',
                        'message': self.env._('Failed to upload: No file selected or file is empty.'),
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }

            path = self.env['ir.config_parameter'].sudo().get_str(
                'dropbox_integration.folder_id') or ''
            path = path.strip().rstrip('/')
            if path and not path.startswith('/'):
                path = '/' + path
            file_name = self.file_name or 'file'
            dropbox_destination = f"{path}/{file_name}" if path else f"/{file_name}"

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    dbx.files_upload(file_data, dropbox_destination)
                    break
                except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    raise

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': self.env._('File has been uploaded successfully.'),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        except (dropbox.exceptions.DropboxException, requests.exceptions.RequestException) as e:
            error_msg = str(e)
            if 'files.content.write' in error_msg or 'not permitted to access this endpoint' in error_msg:
                user_msg = self.env._(
                    "Dropbox Permission Error: Your Dropbox App is missing the required "
                    "'files.content.write' scope. Please enable this scope in the Dropbox App Console "
                    "(under the Permissions tab), then re-authenticate Dropbox in Odoo Settings."
                )
            elif 'SSLEOFError' in error_msg or 'EOF occurred in violation of protocol' in error_msg:
                user_msg = self.env._(
                    "SSL/Network Error: Connection to Dropbox was interrupted. "
                    "This can happen due to network/firewall/proxy drops or missing app permissions. "
                    "Please verify your network and Dropbox App permissions."
                )
            else:
                user_msg = error_msg

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': self.env._('Failed to upload: %s', user_msg),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
