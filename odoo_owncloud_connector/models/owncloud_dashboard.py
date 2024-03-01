# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
import os
import owncloud
from odoo import api, models


class OwnCloudDashboard(models.Model):
    """OwnCloud Dashboard model viewing all the files from ownCloud"""
    _name = 'owncloud.dashboard'
    _description = 'Dashboard Model'

    @api.model
    def action_owncloud_view_files(self):
        """Import all files from ownCloud and show in dashboard"""
        domain = self.env['ir.config_parameter'].get_param(
            'odoo_owncloud_connector.owncloud_domain')
        user_name = self.env['ir.config_parameter'].get_param(
            'odoo_owncloud_connector.owncloud_user_name')
        password = self.env['ir.config_parameter'].get_param(
            'odoo_owncloud_connector.owncloud_password')
        folder = self.env['ir.config_parameter'].get_param(
            'odoo_owncloud_connector.owncloud_folder')
        if not domain or not user_name or not password or not folder:
            return ['e', "Please configure the credentials."]
        try:
            oc_access = owncloud.Client(domain)
            oc_access.login(user_name, password)
            file = []
            for file_name in [file.name for file in
                              oc_access.list('/' + folder)]:
                link_info = oc_access.share_file_with_link(
                    '/' + folder + '/' + file_name)
                file_info = oc_access.file_info('/' + folder + '/' + file_name)
                size_bytes = round(
                    int(file_info.attributes['{DAV:}getcontentlength']) / 1024,
                    1)
                if size_bytes > 1024:
                    size = str(round(int(file_info.attributes[
                                             '{DAV:}getcontentlength']) / (
                                             1024 * 1024), 1)) + ' MB'
                else:
                    size = str(round(int(file_info.attributes[
                                             '{DAV:}getcontentlength']) / 1024,
                                     1)) + ' KB'
                file.append(
                    [file_name, link_info.get_link(), str.upper(
                        os.path.splitext(file_name)[1].replace('.', '')),
                     size])
            oc_access.logout()
            return file
        except Exception as e:
            return ['e', e]

    def action_delete_files(self, *args):
        """Function for delete the file from dashboard and ownCloud storage"""
        domain = self.env['ir.config_parameter'].get_param(
            'odoo_owncloud_connector.owncloud_domain')
        user_name = self.env['ir.config_parameter'].get_param(
            'odoo_owncloud_connector.owncloud_user_name')
        password = self.env['ir.config_parameter'].get_param(
            'odoo_owncloud_connector.owncloud_password')
        folder = self.env['ir.config_parameter'].get_param(
            'odoo_owncloud_connector.owncloud_folder')
        try:
            oc_access = owncloud.Client(domain)
            oc_access.login(user_name, password)
            oc_access.delete('/' + folder + '/' + args[0])
            oc_access.logout()
            return True
        except Exception as e:
            return ['e', e]
