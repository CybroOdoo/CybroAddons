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
import json
import requests
from odoo import api, fields, models
from odoo.tools import html2plaintext


class MailMessage(models.Model):
    """
    This class is inherited for adding an extra field and
    override the create function
    Methods:
        create(values_list):
            extends create() to create comment in  Jira
    """
    _inherit = 'mail.message'

    message_id_jira = fields.Integer(string='Message ID',
                                     help='ID for the comments in Jira.')

    @api.model_create_multi
    def create(self, values_list):
        """ For creating comment in  Jira and comments in the chatter """
        message = super(MailMessage, self).create(values_list)
        if message.message_id_jira == 0:
            ir_config_parameter = self.env['ir.config_parameter'].sudo()
            if ir_config_parameter.get_param('odoo_jira_connector.connection'):
                url = ir_config_parameter.get_param('odoo_jira_connector.url')
                user = ir_config_parameter.get_param(
                    'odoo_jira_connector.user_id_jira')
                password = ir_config_parameter.get_param(
                    'odoo_jira_connector.api_token')
                if message.model == 'project.task':
                    task = self.env['project.task'].browse(message.res_id)
                    current_message = str(html2plaintext(message.body))
                    response = requests.get(
                        f'{url}rest/api/3/issue/{task.task_id_jira}/comment',
                        headers={
                            'Accept': 'application/json',
                            'Content-Type': 'application/json'},
                        auth=(user, password))
                    data = response.json()
                    if response.status_code == 200:
                        list_of_comments_jira = [
                            str(comments['body']['content'][0]['content'][0][
                                    'text']) for comments in data['comments']]
                        if current_message not in list(
                                filter(None, list_of_comments_jira)):
                            data = json.dumps({
                                'body': {
                                    'type': 'doc',
                                    'version': 1,
                                    'content': [{
                                        'type': 'paragraph',
                                        'content': [{
                                            'text': current_message,
                                            'type': 'text'
                                        }]
                                    }]
                                }
                            })
                            response = requests.post(
                                url + 'rest/api/3/issue/%s/comment' % (
                                    task.task_id_jira), headers={
                                    'Accept': 'application/json',
                                    'Content-Type': 'application/json'},
                                data=data, auth=(user, password))
                            data = response.json()
                            message.write({'message_id_jira': data.get('id')})
        return message
