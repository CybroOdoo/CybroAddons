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
import owncloud
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class OwncloudUpload(models.TransientModel):
    """ Wizard model for file upload in to ownCloud storage"""
    _name = "owncloud.upload"
    _description = 'Wizard for File Upload'

    file = fields.Binary(string="Attachment", help="Select a file to upload")
    file_name = fields.Char(string="File Name",
                            help="Name of the file to upload")

    def action_owncloud_upload_file(self):
        """Function for upload the file in to Owncloud storage"""
        attachment = self.env["ir.attachment"].search(
            ['|', ('res_field', '!=', False), ('res_field', '=', False),
             ('res_id', '=', self.id),
             ('res_model', '=', 'owncloud.upload')])
        domain = self.env['ir.config_parameter'].get_param(
            'odoo_owncloud_connector.owncloud_domain')
        user_name = self.env['ir.config_parameter'].get_param(
            'odoo_owncloud_connector.owncloud_user_name')
        password = self.env['ir.config_parameter'].get_param(
            'odoo_owncloud_connector.owncloud_password')
        folder = self.env['ir.config_parameter'].get_param(
            'odoo_owncloud_connector.owncloud_folder')
        if not domain or not user_name or not password or not folder:
            raise UserError(_('Please configure the credentials.'))
        try:
            oc_access = owncloud.Client(domain)
            oc_access.login(user_name, password)
            values = []
            for file in oc_access.list('/'):
                if file.path[-1] == '/':
                    file.path = file.path[:-1]
                values.append(file.path)
            if '/' + folder in values:
                oc_access.put_file('/' + folder + '/' + self.file_name,
                                   attachment._full_path(
                                       attachment.store_fname))
            oc_access.logout()
        except Exception as e:
            raise ValidationError(_(
                'Failed to Upload Files ( %s .)' % e))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': "Your file uploaded successfully.",
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def credentials_checking(self):
        """Checking the credentials while uploading the file"""
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
            values = []
            for file in oc_access.list('/'):
                if file.path[-1] == '/':
                    file.path = file.path[:-1]
                values.append(file.path)
            if '/' + folder in values:
                return True
        except Exception:
            return False
