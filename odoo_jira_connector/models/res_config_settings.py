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
import json
import os
import re
import requests
from requests.auth import HTTPBasicAuth
from odoo import fields, models, _
import logging
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)

# The Header parameters
HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
JIRA_HEADERS = {
    'Accept': 'application/json'
}
ATTACHMENT_HEADERS = {
    'X-Atlassian-Token': 'no-check'
}


class ResConfigSettings(models.TransientModel):
    """ This class is inheriting the model res.config.settings It contains
    fields and functions for the model.
    Methods:
        get_values():
            extends get_values() to include new config parameters
        set_values():
            extends set_values() to include new config parameters
        action_test_connection():
            action to perform when clicking on the 'Test Connection'
            button.
        action_export_to_jira():
            action to perform when clicking on the 'Export/Sync Project'
            button.
        action_import_from_jira():
            action to perform when clicking on the 'Export Users' button.
        action_export_users():
            action to perform when clicking on the 'Reset to Draft' button.
        action_import_users():
            action to perform when clicking on the 'Import Users' button.
        _export_attachments(attachments, attachment_url):
            it is used to export the given attachments to Jira.
        find_attachment_type(attachment):
           it is used to find the attachment type for the given attachment.
    """
    _inherit = 'res.config.settings'

    url = fields.Char(
        string='URL', config_parameter='odoo_jira_connector.url',
        help='Your Jira URL: E.g. https://yourname.atlassian.net/')
    user_id_jira = fields.Char(
        string='User Name', help='E.g. yourmail@gmail.com ',
        config_parameter='odoo_jira_connector.user_id_jira')
    api_token = fields.Char(string='API Token', help='API token in your Jira.',
                            config_parameter='odoo_jira_connector.api_token')
    connection = fields.Boolean(
        string='Connection', default=False, help='To identify the connection.',
        config_parameter='odoo_jira_connector.connection')
    export_project_count = fields.Integer(
        string='Export Project Count', default=0, readonly=True,
        help='Number of export projects.',
    )
    export_task_count = fields.Integer(
        string='Export Task Count', default=0, readonly=True,
        help='Number of export tasks.',
    )
    import_project_count = fields.Integer(
        string='Import Project Count',
        help='Number of import project.', readonly=True,
    )
    import_task_count = fields.Integer(
        string='Import Task Count',
        help='Number of import tasks.', readonly=True,
    )
    automatic = fields.Boolean(string='Automatic',
                               help='to make export/import data automated '
                                    'while creating it on configured Jira '
                                    'account.',
                               config_parameter='odoo_jira_connector.automatic')

    def action_test_connection(self):
        """ Test the connection to Jira
        Raises: ValidationError: If the credentials are invalid.
        Returns:
            dict: client action for displaying notification
        """
        try:
            # Create an authentication object, using registered email-ID, and
            # token received.
            auth = HTTPBasicAuth(self.user_id_jira, self.api_token)
            response = requests.request('GET',
                                        self.url + 'rest/api/2/project',
                                        headers=JIRA_HEADERS, auth=auth)
            if response.status_code == 200 and 'expand' in response.text:
                self.env['ir.config_parameter'].sudo().set_param(
                    'odoo_jira_connector.connection', True)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'success',
                        'message': _(
                            'Test connection to Jira successful.'),
                        'next': {
                            'type': 'ir.actions.act_window_close'
                        }
                    }
                }
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'message': _('Please Enter Valid Credentials.'),
                    'next': {
                        'type': 'ir.actions.act_window_close'
                    }
                }
            }
        except Exception as e:
            raise ValidationError(_('Please Enter Valid Credentials.'))

    def action_export_to_jira(self):
        """ Exporting All The Projects And Corresponding Tasks to Jira,
        and updating the project or task on Jira if it is updated in Odoo.
        """

        auth = HTTPBasicAuth(self.user_id_jira, self.api_token)
        response = requests.request('GET', self.url + 'rest/api/2/project',
                                    headers=JIRA_HEADERS, auth=auth)

        projects = json.dumps(json.loads(response.text), sort_keys=True,
                              indent=4, separators=(',', ': '))
        project_json = json.loads(projects)
        name_list = [project['name'] for project in project_json]
        id_list = [project['id'] for project in project_json]
        odoo_projects = self.env['project.project'].search(
            [('project_id_jira', 'in', id_list)])
        for project in odoo_projects:
            if project.jira_project_key:
                project_keys = project.jira_project_key
            else:
                key = project.name.upper()
                project_key = key[:3] + '1' + key[-3:]
                project_keys = project_key.replace(' ', '')
            response = requests.get(
                self.url + 'rest/api/3/search', headers=HEADERS,
                params={'jql': 'project = %s' % project_keys},
                auth=(self.user_id_jira, self.api_token))
            data = response.json()
            issue_keys = [issue.get('key') for issue in data.get('issues', {})]
            tasks = self.env['project.task'].search(
                [('project_id', '=', project.id)])
            for task in tasks:
                attachment_url = self.url + 'rest/api/3/issue/%s/' \
                                            'attachments' % task.task_id_jira
                comment_url = self.url + 'rest/api/3/issue/%s/comment' % (
                    task.task_id_jira)
                if str(task.task_id_jira) in issue_keys:
                    messages = self.env['mail.message'].search(
                        ['&', ('res_id', '=', task.id),
                         ('model', '=', 'project.task')])
                    attachments = self.env['ir.attachment'].search(
                        [('res_id', '=', task.id)])
                    self._export_attachments(attachments, attachment_url)
                    response = requests.get(
                        comment_url, headers=HEADERS, auth=(
                            self.user_id_jira, self.api_token))
                    data = response.json()
                    jira_comment_list = []
                    for comments in data['comments']:
                        content = comments.get('body', {}).get('content', [])
                        if content and isinstance(content, list) and content[
                            0].get('type') == 'paragraph':
                            text = content[0]['content'][0].get('text')
                            if text:
                                jira_comment_list.append(str(text))
                    odoo_comment_list = [str(
                        html2plaintext(chat.body)) for chat in messages if
                        str(html2plaintext(
                            chat.body)) not in jira_comment_list]
                    comment_list = list(filter(None, odoo_comment_list))
                    if len(comment_list) > 0:
                        for comment in comment_list:
                            data = json.dumps({
                                'body': {
                                    'type': 'doc',
                                    'version': 1,
                                    'content': [{
                                        'type': 'paragraph',
                                        'content': [{
                                            'text': comment,
                                            'type': 'text'
                                        }]}
                                    ]}
                            })
                            requests.post(
                                comment_url, headers=HEADERS, data=data,
                                auth=(self.user_id_jira, self.api_token))
                else:
                    payload = json.dumps({
                        'fields': {
                            'project':
                                {
                                    'key': project_keys
                                },
                            'summary': task.name,
                            'description': task.description,
                            'issuetype': {
                                'name': 'Task'
                            }
                        }
                    })
                    response = requests.post(
                        self.url + '/rest/api/2/issue', headers=HEADERS,
                        data=payload, auth=(self.user_id_jira, self.api_token))
                    data = response.json()
                    task.task_id_jira = data['key']
                    self.env['ir.config_parameter'].sudo().set_param(
                        'odoo_jira_connector.export_task_count', int(
                            self.env['ir.config_parameter'].sudo().get_param(
                                'odoo_jira_connector.export_task_count')) + 1)
                    messages = self.env['mail.message'].search(
                        ['&', ('res_id', '=', task.id),
                         ('model', '=', 'project.task')])
                    attachments = self.env['ir.attachment'].search(
                        [('res_id', '=', task.id)])
                    self._export_attachments(attachments, attachment_url)
                    for chat in messages:
                        data = json.dumps({
                            'body': {
                                'type': 'doc',
                                'version': 1,
                                'content': [{
                                    'type': 'paragraph',
                                    'content': [{
                                        'text': str(html2plaintext(chat.body)),
                                        'type': 'text'}]
                                }]
                            }
                        })
                        requests.post(
                            comment_url, headers=HEADERS, data=data,
                            auth=(self.user_id_jira, self.api_token))
        odoo_projects = self.env['project.project'].search(
            [('project_id_jira', 'not in', id_list),
             ('name', 'not in', name_list)])
        for project in odoo_projects:
            key = project.name.upper()
            project_key = key[:3] + '1' + key[-3:]
            project_keys = project_key.replace(' ', "")
            auth = HTTPBasicAuth(self.user_id_jira, self.api_token)
            project_payload = {
                'name': project.name,
                'key': project_keys,
                'templateKey': 'com.pyxis.greenhopper.jira:gh-simplified'
                               '-kanban-classic'
            }
            response = requests.request(
                'POST', self.url + 'rest/simplified/latest/project',
                data=json.dumps(project_payload), headers=HEADERS, auth=auth)
            data = response.json()
            if 'projectId' in data:
                project.write({
                    'project_id_jira': data['projectId'],
                    'jira_project_key': data['projectKey']
                })
                self.env['ir.config_parameter'].sudo().set_param(
                    'odoo_jira_connector.export_project_count',
                    int(self.env['ir.config_parameter'].sudo().get_param(
                        'odoo_jira_connector.export_project_count')) + 1)
                # for creating a new task inside the project
                tasks = self.env['project.task'].search(
                    [('project_id', '=', project.id)])
                for task in tasks:
                    payload = json.dumps({
                        'fields': {
                            'project': {
                                'key': project_keys
                            },
                            'summary': task.name,
                            'description': task.description,
                            'issuetype': {
                                'name': 'Task'
                            }
                        }
                    })
                    response2 = requests.post(
                        self.url + '/rest/api/2/issue', headers=HEADERS,
                        data=payload, auth=(self.user_id_jira, self.api_token))
                    data = response2.json()
                    task.task_id_jira = data['key']
                    attachment_url = self.url + 'rest/api/3/issue/%s/' \
                                                'attachments' % task.task_id_jira
                    comment_url = self.url + 'rest/api/3/issue/%s/comment' % (
                        task.task_id_jira)
                    self.env['ir.config_parameter'].sudo().set_param(
                        'odoo_jira_connector.export_task_count', int(
                            self.env['ir.config_parameter'].sudo().get_param(
                                'odoo_jira_connector.export_task_count')) + 1)
                    messages = self.env['mail.message'].search(
                        ['&', ('res_id', '=', task.id),
                         ('model', '=', 'project.task')])
                    attachments = self.env['ir.attachment'].search(
                        [('res_id', '=', task.id)])
                    self._export_attachments(attachments, attachment_url)
                    for message in messages:
                        data = json.dumps({
                            'body': {
                                'type': 'doc',
                                'version': 1,
                                'content': [{
                                    'type': 'paragraph',
                                    'content': [{
                                        'text': str(
                                            html2plaintext(message.body)),
                                        'type': 'text'}]
                                }]
                            }
                        })
                        requests.post(comment_url, headers=HEADERS, data=data,
                                      auth=(self.user_id_jira, self.api_token))

            elif 'errors' in data and 'projectName' in data['errors']:
                raise ValidationError(
                    "A project with the names already exists in Jira. Please "
                    "rename the project to export as a new project.")
            elif 'errors' in data and 'projectKey' in data['errors']:
                raise ValidationError(data['errors']['projectKey'])

    def action_export_users(self):
        """ Exporting all the users from Odoo to Jira, and updating the user's
        information on Jira if it has been updated in Odoo
        Raises: ValidationError: If the credentials are not valid.
        """
        response = requests.get(
            self.url + 'rest/api/2/users/search', headers=HEADERS,
            auth=(self.user_id_jira, self.api_token))
        data = response.json()
        issue_keys = [issue['accountId'] for issue in data]
        users = self.env['res.users'].search(
            [('jira_user_key', 'in', issue_keys)])
        non_jira_users = self.env['res.users'].search(
            [('jira_user_key', 'not in', issue_keys)])
        if users:
            for user_data in data:
                for user in users:
                    if user_data['accountId'] == user.jira_user_key:
                        user_data.update({
                            'displayName': user.name
                        })
        if non_jira_users:
            regex = '^\S+@\S+\.\S+$'
            for user in non_jira_users:
                objs = re.search(regex, user.login)
                if objs:
                    if objs.string == str(user.login):
                        payload = json.dumps({
                            'emailAddress': user.login,
                            'displayName': user.name,
                            'name': user.name
                        })
                        response = requests.post(
                            self.url + 'rest/api/3/user', headers=HEADERS,
                            data=payload,
                            auth=(self.user_id_jira, self.api_token))
                        data = response.json()
                        user.write({
                            'jira_user_key': data['accountId']
                        })
                    else:
                        raise ValidationError('Invalid E-mail address.')

    def action_import_users(self):
        """ Importing all the users from Jira to Odoo, and updating the user's
        information on Odoo if it has been updated in Jira.
        """
        response = requests.get(
            self.url + 'rest/api/2/users/search', headers=HEADERS,
            auth=(self.user_id_jira, self.api_token))
        data = response.json()
        for user_data in data:
            users = self.env['res.users'].sudo().search(
                [('login', '=', user_data['displayName'])])
            if users:
                users.write({
                    'jira_user_key': user_data['accountId']
                })
            else:
                self.env['res.users'].create({
                    'login': user_data['displayName'],
                    'name': user_data['displayName'],
                    'jira_user_key': user_data['accountId'],
                })

    def _export_attachments(self, attachments, attachment_url):
        """ To find the corresponding attachment type in the attachment model
        Args:
           attachments (model.Model): values for creating new records.
           attachment_url (str): URL for the attachment.
        """
        for attachment in attachments:
            attachment_type = self.find_attachment_type(attachment)
            if attachment.datas and attachment_type in ('pdf', 'xlsx', 'jpg'):
                temp_file_path = f'/tmp/temp.{attachment_type}'
                binary_data = base64.b64decode(attachment.datas)
                # Save the binary data to a file
                with open(temp_file_path, 'wb') as file:
                    file.write(binary_data)
                if attachment_type == 'jpg' and os.path.splitext(
                        temp_file_path)[1].lower() != '.jpg':
                    # Rename the saved file to its corresponding JPG file format
                    file_path = os.path.splitext(temp_file_path)[0] + '.jpg'
                    os.rename(temp_file_path, file_path)
                    temp_file_path = file_path
                attachment_file = {
                    'file': (attachment.name, open(temp_file_path, 'rb'))
                }
                requests.post(attachment_url, headers=ATTACHMENT_HEADERS,
                              files=attachment_file,
                              auth=(self.user_id_jira, self.api_token))

    def find_attachment_type(self, attachment):
        """ To find the corresponding attachment type in the attachment model
        Args:
           attachment (model.Model): attachment to fetch the type.
        Returns:
            str: the attachment type
        """
        if attachment.mimetype == 'application/pdf':
            return 'pdf'
        if attachment.mimetype == 'image/png':
            return 'jpg'
        if attachment.mimetype == 'application/vnd.openxmlformats-' \
                                  'officedocument.spreadsheetml.sheet':
            return 'xlsx'
        return ''

    def action_import_from_jira(self):
        """ Import projects, tasks, comments, and attachments from Jira to Odoo.
            Updates existing tasks if modified in Jira. Handles text, emojis, and image attachments without duplication.
        """
        auth = HTTPBasicAuth(self.user_id_jira, self.api_token)

        # Fetch Jira projects
        response = requests.get(f"{self.url}rest/api/2/project",
                                headers=JIRA_HEADERS, auth=auth)
        response.raise_for_status()
        projects = response.json()

        odoo_projects = self.env['project.project'].search([])
        odoo_project_map = {p.project_id_jira: p.id for p in odoo_projects}

        for project_data in projects:
            jira_id = int(project_data['id'])
            name = project_data['name']
            key = project_data['key']

            # Create or get Odoo project
            if jira_id in odoo_project_map:
                project_id = odoo_project_map[jira_id]
                project = self.env['project.project'].browse(project_id)
            else:
                project = self.env['project.project'].create({
                    'name': name,
                    'project_id_jira': jira_id,
                    'jira_project_key': key
                })
                self.import_project_count += 1
                odoo_project_map[jira_id] = project.id

            # Fetch issues for the project
            response = requests.get(
                f"{self.url}rest/api/3/search",
                headers=JIRA_HEADERS,
                params={'jql': f'project = {key}'},
                auth=auth
            )
            response.raise_for_status()
            issues = response.json().get('issues', [])

            odoo_tasks = self.env['project.task'].search(
                [('project_id', '=', project.id)])
            task_jira_ids = {task.task_id_jira: task.id for task in odoo_tasks}

            for issue in issues:
                issue_key = issue['key']

                # Create or get Odoo task
                if issue_key in task_jira_ids:
                    task = self.env['project.task'].browse(
                        task_jira_ids[issue_key])
                else:
                    task = self.env['project.task'].create({
                        'project_id': project.id,
                        'name': issue['fields']['summary'],
                        'task_id_jira': issue_key
                    })
                    self.import_task_count += 1

                # Fetch issue attachments
                attachment_url = f"{self.url}rest/api/3/issue/{issue_key}?fields=attachment"
                try:
                    attachment_response = requests.get(attachment_url,
                                                       headers=JIRA_HEADERS,
                                                       auth=auth)
                    attachment_response.raise_for_status()
                    issue_attachments = {att['filename']: att for att in
                                         attachment_response.json().get(
                                             'fields', {}).get('attachment',
                                                               [])}
                except requests.RequestException as e:
                    _logger.error(
                        f"Failed to fetch attachments for issue {issue_key}: {str(e)}")
                    issue_attachments = {}

                # Fetch comments
                comment_url = f"{self.url}rest/api/3/issue/{issue_key}/comment"
                response = requests.get(comment_url, headers=JIRA_HEADERS,
                                        auth=auth)
                response.raise_for_status()
                comments = response.json().get('comments', [])

                # Get existing Odoo comments and attachments to avoid duplicates
                messages = self.env['mail.message'].search(
                    [('res_id', '=', task.id), ('model', '=', 'project.task')])
                odoo_comment_ids = {
                    m.message_id_jira: html2plaintext(m.body).strip() for m in
                    messages if m.message_id_jira}
                existing_attachments = self.env['ir.attachment'].search([
                    ('res_model', '=', 'project.task'),
                    ('res_id', '=', task.id)
                ])
                existing_attachment_names = {att.name for att in
                                             existing_attachments}

                for comment in comments:
                    jira_comment_id = int(comment['id'])
                    text_content = ""
                    attachments = []
                    comment_body = comment.get('body', {}).get('content', [])

                    # Process comment content
                    for block in comment_body:
                        if block.get('type') == 'paragraph':
                            for item in block.get('content', []):
                                if item.get('type') == 'text':
                                    text_content += item.get('text', '') + " "
                                elif item.get('type') == 'emoji':
                                    text_content += item.get('attrs', {}).get(
                                        'text', '') + " "
                        elif block.get('type') == 'mediaSingle':
                            for item in block.get('content', []):
                                if item.get('type') == 'media':
                                    media_attrs = item.get('attrs', {})
                                    media_id = media_attrs.get('id')
                                    filename = media_attrs.get('alt',
                                                               f"attachment-{media_id}")
                                    if filename in issue_attachments:
                                        attachment = issue_attachments[filename]
                                        if attachment[
                                            'filename'] not in existing_attachment_names:
                                            attachments.append({
                                                'url': attachment['content'],
                                                'filename': attachment[
                                                    'filename'],
                                                'media_id': media_id
                                            })
                                    else:
                                        _logger.warning(
                                            f"Attachment '{filename}' (media_id: {media_id}) not found for issue {issue_key}")

                    # Import text comment if not already in Odoo
                    text_content = text_content.strip()
                    if text_content and jira_comment_id not in odoo_comment_ids:
                        message = task.message_post(body=text_content)
                        message.write({'message_id_jira': jira_comment_id})
                        odoo_comment_ids[jira_comment_id] = text_content

                    # Import attachments
                    for attachment in attachments:
                        try:
                            response = requests.get(attachment['url'],
                                                    headers=JIRA_HEADERS,
                                                    auth=auth, stream=True)
                            response.raise_for_status()
                            attachment_data = base64.b64encode(
                                response.content).decode('utf-8')
                            self.env['ir.attachment'].create({
                                'name': attachment['filename'],
                                'datas': attachment_data,
                                'res_model': 'project.task',
                                'res_id': task.id,
                                'mimetype': self._guess_mimetype(
                                    attachment['filename']),
                            })
                            existing_attachment_names.add(
                                attachment['filename'])
                        except requests.RequestException as e:
                            _logger.error(
                                f"Failed to download attachment '{attachment['filename']}' (media_id: {attachment['media_id']}, URL: {attachment['url']}) for task {task.task_id_jira}: {str(e)}")

    def _guess_mimetype(self, filename):
        """ Guess the MIME type based on the file extension """
        from mimetypes import guess_type
        mime_type, _ = guess_type(filename)
        return mime_type or 'application/octet-stream'
