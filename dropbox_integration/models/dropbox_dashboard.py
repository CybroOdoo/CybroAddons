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
import requests

from odoo import api, fields, models
from odoo.exceptions import AccessError


class DropboxDashboard(models.Model):
    """ Dashboard model that stores Dropbox credentials. """
    _name = 'dropbox.dashboard'
    _description = 'Stores Dropbox Credentials'

    dropbox_client_id = fields.Char(string='Dropbox Client ID',
                                    help="Dropbox Client ID")
    dropbox_client_secret = fields.Char(string='Dropbox Client Secret',
                                        help="Dropbox Client Secret")
    dropbox_refresh_token = fields.Char(string='Dropbox Refresh Token',
                                        help="Dropbox Refresh Token")

    @api.model
    def action_import_files(self, *args, **kwargs):
        """ Import files and directory items from Dropbox. """
        if not self.env.user.has_group('base.group_user'):
            raise AccessError(self.env._("Access Denied: Only internal users can access Dropbox files."))
        try:
            access = self.env['dropbox.dashboard'].sudo().search(
                [], order='id desc', limit=1)
            if not access or not access.dropbox_refresh_token:
                return False
            dbx = dropbox.Dropbox(
                app_key=access.dropbox_client_id,
                app_secret=access.dropbox_client_secret,
                oauth2_refresh_token=access.dropbox_refresh_token,
            )
            path = self.env['ir.config_parameter'].sudo().get_str(
                'dropbox_integration.folder_id') or ''
            path = path.strip()
            if path == '/':
                path = ''
            elif path and not path.startswith('/'):
                path = '/' + path

            response = dbx.files_list_folder(path=path)
            entries = list(response.entries)
            while getattr(response, 'has_more', False):
                response = dbx.files_list_folder_continue(cursor=response.cursor)
                entries.extend(response.entries)

            folder_cls = getattr(getattr(dropbox, 'files', None), 'FolderMetadata', None)
            file_cls = getattr(getattr(dropbox, 'files', None), 'FileMetadata', None)

            data = {}
            for entry in entries:
                is_folder = (folder_cls and isinstance(entry, folder_cls)) or getattr(entry, '.tag', '') == 'folder'
                if is_folder:
                    folder_path = getattr(entry, 'path_display', '') or getattr(entry, 'path_lower', '') or ''
                    data[entry.name] = f"https://www.dropbox.com/home{folder_path}"
                    continue

                is_file = (file_cls and isinstance(entry, file_cls)) or getattr(entry, '.tag', '') == 'file'
                path_to_get = getattr(entry, 'path_lower', None) or getattr(entry, 'path_display', None)

                if (is_file or not folder_cls) and path_to_get:
                    try:
                        file_res = dbx.files_get_temporary_link(path=path_to_get)
                        name = getattr(getattr(file_res, 'metadata', None), 'name', getattr(entry, 'name', 'file'))
                        data[name] = file_res.link
                    except Exception:
                        file_path = getattr(entry, 'path_display', '') or path_to_get
                        data[getattr(entry, 'name', 'file')] = f"https://www.dropbox.com/home{file_path}"
                elif hasattr(entry, 'name'):
                    data[entry.name] = f"https://www.dropbox.com/home/{entry.name}"

            return data
        except (dropbox.exceptions.DropboxException, requests.exceptions.RequestException, OSError) as e:
            return ['e', str(e)]
        except Exception as e:
            return ['e', str(e)]
