# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya B (odoo@cybrosys.com)
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
##############################################################################
import base64
import os
import requests
from odoo import models, fields, api
# The Header parameters
HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json'}


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    attachment_id_jira = fields.Integer(string="Jira ID",
                                        help="Jira id of attachment.")

    @api.model_create_multi
    def create(self, values_list):
        """ For creating attachment in  Jira and attachment in the chatter """
        attachment = super(IrAttachment, self).create(values_list)
        if  values_list and  not values_list[0].get('attachment_id_jira') :
            ir_config_parameter = self.env['ir.config_parameter'].sudo()
            if ir_config_parameter.get_param('odoo_jira_connector.connection'):
                url = ir_config_parameter.get_param('odoo_jira_connector.url')
                user = ir_config_parameter.get_param(
                    'odoo_jira_connector.user_id_jira')
                password = ir_config_parameter.get_param(
                    'odoo_jira_connector.api_token')
                if attachment.res_model == 'project.task':
                    task = self.env['project.task'].browse(attachment.res_id)
                    attachment_url = url + 'rest/api/3/issue/%s/' \
                                           'attachments' % task.task_id_jira
                    attachment_type = (self.env['res.config.settings'].
                                       find_attachment_type(attachment))
                    if attachment.datas and attachment_type in (
                            'pdf', 'xlsx', 'jpg'):
                        temp_file_path = f'/tmp/temp.{attachment_type}'
                        binary_data = base64.b64decode(attachment.datas)
                        # Save the binary data to a file
                        with open(temp_file_path, 'wb') as file:
                            file.write(binary_data)
                        if attachment_type == 'jpg' and os.path.splitext(
                                temp_file_path)[1].lower() != '.jpg':
                            # Rename the saved file to its corresponding JPG
                            # file format
                            file_path = os.path.splitext(temp_file_path)[
                                            0] + '.jpg'
                            os.rename(temp_file_path, file_path)
                            temp_file_path = file_path
                        attachment_file = {
                            'file': (
                                attachment.name, open(temp_file_path, 'rb'))
                        }
                        response = requests.post(attachment_url,
                                                 headers={
                                                     'X-Atlassian-Token':
                                                         'no-check'},
                                                 files=attachment_file,
                                                 auth=(user, password))
                        data = response.json()
                        attachment.write(
                            {'attachment_id_jira': data[0].get('id')})
        return attachment

    def unlink(self):
        """ Overrides the unlink method of attachment to delete an attachment
        in Jira when we delete the attachment in Odoo"""
        for attachment in self:
            jira_connection = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.connection')
            if jira_connection:
                jira_url = self.env['ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.url', '')
                user = self.env['ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.user_id_jira')
                password = self.env['ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.api_token')
                if attachment.attachment_id_jira:
                    requests.delete(
                        jira_url + '/rest/api/3/attachment/' +
                        str(attachment.attachment_id_jira),
                        headers=HEADERS, auth=(user, password))
        return super(IrAttachment, self).unlink()
