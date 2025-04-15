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
import logging
from odoo import api, fields, models
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)

class MailMessage(models.Model):
    """
    This class is inherited for adding an extra field and
    override the create function
    Methods:
        create(values_list):
            Extends create() to create comments in Jira, handling text and attachments
    """
    _inherit = 'mail.message'

    message_id_jira = fields.Integer(string='Message ID',
                                    help='ID for the comments in Jira.')

    @api.model_create_multi
    def create(self, values_list):
        """ For creating comments in Jira and comments in the chatter """
        messages = super(MailMessage, self).create(values_list)
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        if not ir_config_parameter.get_param('odoo_jira_connector.connection'):
            return messages

        url = ir_config_parameter.get_param('odoo_jira_connector.url')
        user = ir_config_parameter.get_param('odoo_jira_connector.user_id_jira')
        password = ir_config_parameter.get_param('odoo_jira_connector.api_token')
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        for message in messages:
            if message.message_id_jira == 0 and message.model == 'project.task':
                task = self.env['project.task'].browse(message.res_id)
                if not task.task_id_jira:
                    continue

                # Extract text content from the message body
                current_message = str(html2plaintext(message.body)).strip()
                comment_url = f'{url}rest/api/3/issue/{task.task_id_jira}/comment'

                # Fetch existing Jira comments to avoid duplicates
                try:
                    response = requests.get(comment_url, headers=headers, auth=(user, password))
                    response.raise_for_status()
                    data = response.json()
                except requests.RequestException as e:
                    _logger.error(f"Failed to fetch Jira comments for task {task.task_id_jira}: {str(e)}")
                    continue

                # Parse Jira comments to extract text content
                list_of_comments_jira = []
                for comment in data.get('comments', []):
                    text_content = ""
                    comment_body = comment.get('body', {}).get('content', [])
                    for content_block in comment_body:
                        if content_block.get('type') == 'paragraph':
                            for content_item in content_block.get('content', []):
                                if content_item.get('type') == 'text':
                                    text_content += content_item.get('text', '') + " "
                                elif content_item.get('type') == 'emoji':
                                    text_content += content_item.get('attrs', {}).get('text', '') + " "
                    if text_content.strip():
                        list_of_comments_jira.append(text_content.strip())

                # Post comment to Jira if it's new
                if current_message and current_message not in list_of_comments_jira:
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
                    try:
                        response = requests.post(comment_url, headers=headers, data=data,
                                                auth=(user, password))
                        response.raise_for_status()
                        data = response.json()
                        message.write({'message_id_jira': data.get('id')})
                    except requests.RequestException as e:
                        _logger.error(f"Failed to post comment to Jira for task {task.task_id_jira}: {str(e)}")

        return messages
