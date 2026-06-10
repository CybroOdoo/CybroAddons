# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import requests
import base64
import logging
import re
import os
import json
from odoo import fields, models, _
from requests.auth import HTTPBasicAuth
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)
HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'X-Atlassian-Token': 'no-check',
    'User-Agent': 'OdooJiraConnector/18.0'
}
JIRA_HEADERS = {
    'Accept': 'application/json',
    'X-Atlassian-Token': 'no-check',
    'User-Agent': 'OdooJiraConnector/18.0'
}
ATTACHMENT_HEADERS = {
    'X-Atlassian-Token': 'no-check',
    'User-Agent': 'OdooJiraConnector/18.0'
}


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    url = fields.Char(string='URL', config_parameter='odoo_jira_connector.url',
                      help='Your Jira URL: E.g. https://yourname.atlassian.net/')
    user_id_jira = fields.Char(string='User Name',
                               help='E.g. yourmail@gmail.com ',
                               config_parameter='odoo_jira_connector.user_id_jira')
    api_token = fields.Char(string='API Token', help='API token in your Jira.',
                            config_parameter='odoo_jira_connector.api_token')
    connection = fields.Boolean(string='Connection', default=False,
                                help='To identify the connection.',
                                config_parameter='odoo_jira_connector.connection')
    automatic = fields.Boolean(string='Automatic',
                               help='To make export/import data automated while creating it on configured Jira account.',
                               config_parameter='odoo_jira_connector.automatic')

    def action_test_connection(self):
        self.ensure_one()
        if not self.url or not self.user_id_jira or not self.api_token:
            raise UserError(
                _("Please provide the URL, Username, and API Token to test the Jira connection."))

        try:
            url = self.url.rstrip('/') + '/rest/api/2/project'
            auth = HTTPBasicAuth(self.user_id_jira, self.api_token)
            response = requests.get(url, headers=JIRA_HEADERS, auth=auth,
                                    timeout=20)
            if response.ok:
                self.env['ir.config_parameter'].sudo().set_param(
                    'odoo_jira_connector.connection', True)
                message = _('Test connection to Jira successful.')
                notif_type = 'success'
            else:
                message = _(
                    'Failed to connect to Jira. Please check your credentials.')
                notif_type = 'danger'

        except requests.exceptions.RequestException as e:
            _logger.error("Jira connection error: %s", e)
            message = _('Connection to Jira failed: %s') % str(e)
            notif_type = 'danger'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': notif_type,
                'message': message,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

    def action_export_to_jira(self):
        auth = HTTPBasicAuth(self.user_id_jira, self.api_token)
        try:
            response = requests.request('GET', self.url.rstrip('/') + '/rest/api/2/project',
                                        headers=JIRA_HEADERS, auth=auth,
                                        timeout=20)
            response.raise_for_status()
            project_json = response.json()
            if not isinstance(project_json, list):
                _logger.error("Unexpected Jira response for projects: %s", project_json)
                project_json = []
        except Exception as e:
            _logger.error("Failed to fetch projects from Jira: %s", e)
            project_json = []

        name_list = [project.get('name') for project in project_json if
                     isinstance(project, dict) and project.get('name')]
        id_list = []
        for project in project_json:
            if isinstance(project, dict) and project.get('id'):
                try:
                    id_list.append(int(project.get('id')))
                except ValueError:
                    continue

        # Map existing Odoo projects whose names match Jira projects but don't have project_id_jira set
        unmapped_projects = self.env['project.project'].search([
            ('project_id_jira', '=', False),
            ('name', 'in', name_list)
        ])
        for p in unmapped_projects:
            for jira_proj in project_json:
                if isinstance(jira_proj, dict) and jira_proj.get('name') == p.name:
                    try:
                        p.write({
                            'project_id_jira': int(jira_proj.get('id')),
                            'jira_project_key': jira_proj.get('key')
                        })
                    except Exception:
                        pass
                    break

        odoo_projects = self.env['project.project'].search(
            [('project_id_jira', 'in', id_list)])

        project_count = 0
        task_count = 0
        task_skip = 0
        project_skip = 0

        for project in odoo_projects:
            if project.jira_project_key:
                project_keys = project.jira_project_key
                project_skip += 1
            else:
                key = project.name.upper()
                project_key = key[:3] + '1' + key[-3:]
                project_keys = project_key.replace(' ', '')

            # Robust search attempt (New /search/jql fallback to v3/v2)
            search_url = self.url.rstrip('/') + '/rest/api/3/search/jql'
            try:
                response = requests.get(
                    search_url, headers=HEADERS,
                    params={'jql': 'project = "%s"' % project_keys},
                    auth=(self.user_id_jira, self.api_token),
                    timeout=20)
                if response.status_code == 410 or response.status_code == 404:
                    _logger.info("Jira Search /search/jql returned 410/404. Falling back to v3.")
                    search_url = self.url.rstrip('/') + '/rest/api/3/search'
                    response = requests.get(
                        search_url, headers=HEADERS,
                        params={'jql': 'project = "%s"' % project_keys},
                        auth=(self.user_id_jira, self.api_token),
                        timeout=20)
                if response.status_code == 410 or response.status_code == 404:
                    _logger.info("Jira Search API v3 returned 410/404. Falling back to v2.")
                    search_url = self.url.rstrip('/') + '/rest/api/2/search'
                    response = requests.get(
                        search_url, headers=HEADERS,
                        params={'jql': 'project = "%s"' % project_keys},
                        auth=(self.user_id_jira, self.api_token),
                        timeout=20)
                response.raise_for_status()
            except requests.RequestException as e:
                status_code = e.response.status_code if e.response is not None else 'No Response'
                response_text = e.response.text if e.response is not None else str(e)
                _logger.error(f"Jira Search failed for both API v3 and v2. Status: {status_code}. Detail: {response_text}")
                continue

            data = response.json()
            if not isinstance(data, dict):
                _logger.error("Unexpected Jira search response: %s", data)
                data = {}
            issue_keys = [issue.get('key') for issue in data.get('issues', []) if
                          isinstance(issue, dict) and issue.get('key')]
            tasks = self.env['project.task'].search(
                [('project_id', '=', project.id)])

            for task in tasks:
                attachment_url = self.url.rstrip('/') + '/rest/api/2/issue/%s/attachments' % task.task_id_jira
                comment_url = self.url.rstrip('/') + '/rest/api/2/issue/%s/comment' % task.task_id_jira
                if str(task.task_id_jira) in issue_keys:
                    task_skip += 1
                    messages = self.env['mail.message'].search(
                        ['&', ('res_id', '=', task.id),
                         ('model', '=', 'project.task')])
                    attachments = self.env['ir.attachment'].search(
                        [('res_id', '=', task.id)])
                    try:
                        self._export_attachments(attachments, attachment_url)
                    except Exception as e:
                        _logger.warning("Failed to export attachments for task %s: %s", task.task_id_jira, e)
                    try:
                        response = requests.get(comment_url, headers=HEADERS,
                                                auth=(self.user_id_jira,
                                                      self.api_token),
                                                timeout=20)
                        response.raise_for_status()
                        data = response.json()
                    except Exception as e:
                        _logger.warning("Failed to fetch comments for task %s: %s", task.task_id_jira, e)
                        data = {}
                    if not isinstance(data, dict):
                        data = {}
                    jira_comment_list = []
                    for comments in data.get('comments', []):
                        body = comments.get('body')
                        if isinstance(body, dict):
                            # Handle Jira API v3 ADF format
                            content = body.get('content', [])
                            if content and isinstance(content, list) and content[
                                0].get('type') == 'paragraph':
                                text = content[0]['content'][0].get('text')
                                if text:
                                    jira_comment_list.append(str(text))
                        else:
                            # Handle Jira API v2 string format
                            if body:
                                jira_comment_list.append(str(body))
                    odoo_comment_list = [str(html2plaintext(chat.body)) for chat
                                         in messages if str(html2plaintext(
                            chat.body)) not in jira_comment_list]
                    comment_list = list(filter(None, odoo_comment_list))
                    if len(comment_list) > 0:
                        for comment in comment_list:
                            data_payload = json.dumps({
                                'body': {
                                    'type': 'doc',
                                    'version': 1,
                                    'content': [{
                                        'type': 'paragraph',
                                        'content': [{
                                            'text': comment,
                                            'type': 'text'
                                        }]
                                    }
                                    ]}
                            })
                            try:
                                requests.post(comment_url, headers=HEADERS,
                                              data=data_payload, auth=(self.user_id_jira,
                                                               self.api_token),
                                              timeout=20)
                            except Exception as e:
                                _logger.warning("Failed to export comment for task %s: %s", task.task_id_jira, e)
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
                    try:
                        response = requests.post(
                            self.url.rstrip('/') + '/rest/api/2/issue', headers=HEADERS,
                            data=payload, auth=(self.user_id_jira, self.api_token),
                            timeout=20)
                        response.raise_for_status()
                        data = response.json()
                    except Exception as e:
                        _logger.error("Failed to create issue in Jira for task %s: %s", task.name, e)
                        data = {}
                    if isinstance(data, dict) and data.get('key'):
                        task.task_id_jira = data['key']
                        task_count += 1
                        messages = self.env['mail.message'].search(
                            ['&', ('res_id', '=', task.id),
                             ('model', '=', 'project.task')])
                        attachments = self.env['ir.attachment'].search(
                            [('res_id', '=', task.id)])
                        
                        # Correctly update attachment_url and comment_url with the new task key!
                        attachment_url = self.url.rstrip('/') + '/rest/api/2/issue/%s/attachments' % task.task_id_jira
                        comment_url = self.url.rstrip('/') + '/rest/api/2/issue/%s/comment' % task.task_id_jira

                        try:
                            self._export_attachments(attachments, attachment_url)
                        except Exception as e:
                            _logger.warning("Failed to export attachments for new task %s: %s", task.task_id_jira, e)
                        for chat in messages:
                            if not chat.body:
                                continue
                            data_payload = json.dumps({
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
                            try:
                                requests.post(
                                    comment_url, headers=HEADERS, data=data_payload,
                                    auth=(self.user_id_jira, self.api_token),
                                    timeout=20)
                            except Exception as e:
                                _logger.warning("Failed to export comment for new task %s: %s", task.task_id_jira, e)
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
            try:
                response = requests.request('POST',
                                            self.url.rstrip('/') + '/rest/simplified/latest/project',
                                            data=json.dumps(project_payload),
                                            headers=HEADERS, auth=auth,
                                            timeout=20)
                if response.status_code == 201:
                    data = response.json()
                    if isinstance(data, dict) and 'projectId' in data:
                        project.write({
                            'project_id_jira': data['projectId'],
                            'jira_project_key': data.get('projectKey') or project_keys
                        })
                        project_count += 1

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
                            try:
                                response2 = requests.post(self.url.rstrip('/') + '/rest/api/2/issue',
                                                          headers=HEADERS, data=payload,
                                                          auth=(self.user_id_jira,
                                                                self.api_token),
                                                          timeout=20)
                                response2.raise_for_status()
                                data2 = response2.json()
                            except Exception as e:
                                _logger.warning("Failed to create task in Jira: %s", e)
                                data2 = {}
                            if isinstance(data2, dict) and data2.get('key'):
                                task.task_id_jira = data2['key']
                                task_count += 1
                                attachment_url = self.url.rstrip('/') + '/rest/api/2/issue/%s/attachments' % task.task_id_jira
                                comment_url = self.url.rstrip('/') + '/rest/api/2/issue/%s/comment' % task.task_id_jira
                                messages = self.env['mail.message'].search(
                                    ['&', ('res_id', '=', task.id),
                                     ('model', '=', 'project.task')])
                                attachments = self.env['ir.attachment'].search(
                                    [('res_id', '=', task.id)])
                                try:
                                    self._export_attachments(attachments, attachment_url)
                                except Exception as e:
                                    _logger.warning("Failed to export attachments for new project task: %s", e)
                                for message in messages:
                                    if not message.body:
                                        continue
                                    data_msg = json.dumps({
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
                                    try:
                                        requests.post(comment_url, headers=HEADERS, data=data_msg,
                                                      auth=(self.user_id_jira, self.api_token),
                                                      timeout=20)
                                    except Exception as e:
                                        _logger.warning("Failed to export comment for new project task: %s", e)
                else:
                    try:
                        data = response.json()
                    except Exception:
                        data = {}
                    if isinstance(data, dict) and 'errors' in data and isinstance(data['errors'], dict) and 'projectName' in data['errors']:
                        raise ValidationError(
                            "A project with the names already exists in Jira. Please "
                            "rename the project to export as a new project.")
                    elif isinstance(data, dict) and 'errors' in data and isinstance(data['errors'], dict) and 'projectKey' in data['errors']:
                        raise ValidationError(data['errors']['projectKey'])
                    else:
                        _logger.error(f"Failed to create project in Jira. Status: {response.status_code}. Content: {response.text}")

            except (requests.exceptions.RequestException, ValueError) as e:
                _logger.error(f"Error during project export to Jira: {str(e)}")
                continue

        message = ""
        if project_count > 0:
            message += _("%d Project(s) exported. ", project_count)
        if task_count > 0:
            message += _("%d Task(s) exported. ", task_count)
        if project_count == 0 and task_count == 0:
            message = _("Success.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': message,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

    def action_import_from_jira(self):
        auth = HTTPBasicAuth(self.user_id_jira, self.api_token)
        try:
            response = requests.get(self.url.rstrip('/') + '/rest/api/2/project',
                                    headers=JIRA_HEADERS, auth=auth,
                                    timeout=20)
            response.raise_for_status()
            projects = response.json()
            if not isinstance(projects, list):
                _logger.error("Unexpected Jira response for projects: %s", projects)
                projects = []
        except Exception as e:
            _logger.error("Failed to fetch projects from Jira: %s", e)
            projects = []
        odoo_projects = self.env['project.project'].search([])
        odoo_project_map = {p.project_id_jira: p.id for p in odoo_projects}

        project_count = 0
        task_count = 0
        project_skip = 0
        task_skip = 0

        for project_data in projects:
            if not isinstance(project_data, dict) or 'id' not in project_data or 'key' not in project_data:
                continue
            try:
                jira_id = int(project_data['id'])
            except (ValueError, TypeError):
                continue
            name = project_data.get('name') or project_data['key']
            key = project_data['key']

            # Create or get Odoo project
            if jira_id in odoo_project_map:
                project_id = odoo_project_map[jira_id]
                project = self.env['project.project'].browse(project_id)
                project_skip += 1
            else:
                project = self.env['project.project'].create([{
                    'name': name,
                    'project_id_jira': jira_id,
                    'jira_project_key': key,
                }])
                project_count += 1

            # Robust search attempt (New /search/jql fallback to v3/v2)
            search_url = self.url.rstrip('/') + "/rest/api/3/search/jql"
            try:
                issue_response = requests.get(
                    search_url,
                    headers=HEADERS,
                    params={'jql': f'project = "{key}"'},
                    auth=auth,
                    timeout=20
                )
                if issue_response.status_code == 410 or issue_response.status_code == 404:
                    _logger.info("Jira Search /search/jql returned 410/404. Falling back to v3.")
                    search_url = self.url.rstrip('/') + "/rest/api/3/search"
                    issue_response = requests.get(
                        search_url,
                        headers=HEADERS,
                        params={'jql': f'project = "{key}"'},
                        auth=auth,
                        timeout=20
                    )
                if issue_response.status_code == 410 or issue_response.status_code == 404:
                    _logger.info("Jira Search API v3 returned 410/404. Falling back to v2.")
                    search_url = self.url.rstrip('/') + "/rest/api/2/search"
                    issue_response = requests.get(
                        search_url,
                        headers=HEADERS,
                        params={'jql': f'project = "{key}"'},
                        auth=auth,
                        timeout=20
                    )
                issue_response.raise_for_status()
            except requests.RequestException as e:
                status_code = e.response.status_code if e.response is not None else 'No Response'
                response_text = e.response.text if e.response is not None else str(e)
                _logger.error(f"Jira Search failed for both API v3 and v2. Status: {status_code}. Detail: {response_text}")
                # We skip this project and continue
                continue

            try:
                issue_json = issue_response.json()
                issues = issue_json.get('issues', []) if isinstance(issue_json, dict) else []
            except Exception:
                issues = []

            odoo_tasks = self.env['project.task'].search(
                [('project_id', '=', project.id)])
            task_jira_ids = {task.task_id_jira: task.id for task in odoo_tasks}

            for issue in issues:
                if not isinstance(issue, dict) or not issue.get('key'):
                    continue
                issue_key = issue['key']

                # Create or get Odoo task
                if issue_key in task_jira_ids:
                    task = self.env['project.task'].browse(
                        task_jira_ids[issue_key])
                    task_skip += 1
                else:
                    fields = issue.get('fields') or {}
                    summary = fields.get('summary') or 'No Summary'
                    task = self.env['project.task'].create([{
                        'project_id': project.id,
                        'name': summary,
                        'task_id_jira': issue_key
                    }])
                    task_count += 1
                # Fetch issue attachments
                attachment_url = self.url.rstrip('/') + f"/rest/api/2/issue/{issue_key}?fields=attachment"
                try:
                    attachment_response = requests.get(attachment_url,
                                                       headers=JIRA_HEADERS,
                                                       auth=auth,
                                                       timeout=20)
                    attachment_response.raise_for_status()
                    try:
                        att_data = attachment_response.json()
                        if not isinstance(att_data, dict):
                            att_data = {}
                    except Exception:
                        att_data = {}
                    issue_attachments = {att.get('filename'): att for att in
                                         att_data.get('fields', {}).get(
                                             'attachment',
                                             []) if isinstance(att, dict) and att.get('filename')}
                except requests.RequestException as e:
                    _logger.error(
                        f"Failed to fetch attachments for issue {issue_key}: {str(e)}")
                    issue_attachments = {}

                # Fetch comments
                comment_url = self.url.rstrip('/') + f"/rest/api/2/issue/{issue_key}/comment"
                response = requests.get(comment_url, headers=JIRA_HEADERS,
                                        auth=auth, timeout=20)
                response.raise_for_status()
                comments = response.json().get('comments', [])

                # Get existing Odoo comments and attachments to avoid duplicates
                messages = self.env['mail.message'].search(
                    [('res_id', '=', task.id), ('model', '=', 'project.task')])
                odoo_comment_ids = {}
                for m in messages:
                    if m.message_id_jira:
                        odoo_comment_ids[int(m.message_id_jira)] = html2plaintext(m.body).strip()
                existing_attachments = self.env['ir.attachment'].search(
                    [('res_model', '=', 'project.task'),
                     ('res_id', '=', task.id)])
                existing_attachment_names = {att.name for att in
                                             existing_attachments}

                for comment in comments:
                    if not isinstance(comment, dict) or 'id' not in comment:
                        continue
                    try:
                        jira_comment_id = int(comment['id'])
                    except (ValueError, TypeError):
                        continue
                    text_content = ""
                    attachments = []

                    # Process comment content
                    comment_body = comment.get('body')
                    if isinstance(comment_body, dict):
                        # Handle v3 ADF
                        body_content = comment_body.get('content', [])
                        if not isinstance(body_content, list):
                            body_content = []
                        for block in body_content:
                            if not isinstance(block, dict):
                                continue
                            if block.get('type') == 'paragraph':
                                block_content = block.get('content', [])
                                if isinstance(block_content, list):
                                    for item in block_content:
                                        if not isinstance(item, dict):
                                            continue
                                        if item.get('type') == 'text':
                                            text_content += item.get('text', '') + " "
                                        elif item.get('type') == 'emoji':
                                            text_content += item.get('attrs', {}).get(
                                                'text', '') + " "
                            elif block.get('type') == 'mediaSingle':
                                block_content = block.get('content', [])
                                if isinstance(block_content, list):
                                    for item in block_content:
                                        if not isinstance(item, dict):
                                            continue
                                        if item.get('type') == 'media':
                                            media_attrs = item.get('attrs', {})
                                            if isinstance(media_attrs, dict):
                                                media_id = media_attrs.get('id')
                                                filename = media_attrs.get('alt',
                                                                           f"attachment-{media_id}")
                                                if filename in issue_attachments:
                                                    attachment = issue_attachments[filename]
                                                    if isinstance(attachment, dict) and attachment.get('filename') and attachment.get('content'):
                                                        if attachment['filename'] not in existing_attachment_names:
                                                            attachments.append({
                                                                'url': attachment['content'],
                                                                'filename': attachment['filename'],
                                                                'media_id': media_id
                                                            })
                    else:
                        # Handle v2 String
                        text_content = str(comment_body) or ""

                    # Import text comment if not already in Odoo
                    text_content = text_content.strip()
                    if text_content and jira_comment_id not in odoo_comment_ids:
                        message = task.message_post(body=text_content)
                        message.write({'message_id_jira': jira_comment_id})
                        if isinstance(odoo_comment_ids, dict):
                            odoo_comment_ids[jira_comment_id] = text_content

                    # Import attachments
                    for attachment in attachments:
                        try:
                            response = requests.get(attachment['url'],
                                                    headers=JIRA_HEADERS,
                                                    auth=auth, stream=True,
                                                    timeout=20)
                            response.raise_for_status()
                            attachment_data = base64.b64encode(
                                response.content).decode('utf-8')
                            self.env['ir.attachment'].create([{
                                'name': attachment['filename'],
                                'datas': attachment_data,
                                'res_model': 'project.task',
                                'res_id': task.id,
                                'mimetype': self._guess_mimetype(
                                    attachment['filename']),
                            }])
                            existing_attachment_names.add(
                                attachment['filename'])
                        except requests.RequestException as e:
                            _logger.error(
                                f"Failed to download attachment '{attachment['filename']}' (media_id: {attachment['media_id']}, URL: {attachment['url']}) for task {task.task_id_jira}: {str(e)}")

        message = ""
        if project_count > 0:
            message += _("%d Project(s) imported. ", project_count)
        if task_count > 0:
            message += _("%d Task(s) imported. ", task_count)
        if project_count == 0 and task_count == 0:
            message = _("Success")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': message,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

    def action_export_users(self):
        try:
            response = requests.get(self.url.rstrip('/') + '/rest/api/2/users/search',
                                    headers=HEADERS,
                                    auth=(self.user_id_jira, self.api_token),
                                    timeout=20)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                _logger.error("Unexpected Jira response (not a list): %s", data)
                data = []
        except Exception as e:
            _logger.error("Failed to fetch users from Jira: %s", e)
            data = []

        issue_keys = [issue.get('accountId') for issue in data if isinstance(issue, dict) and issue.get('accountId')]
        users = self.env['res.users'].search(
            [('jira_user_key', 'in', issue_keys)])
        non_jira_users = self.env['res.users'].search(
            [('jira_user_key', 'not in', issue_keys)])
        user_exported = 0
        user_updated = 0
        user_skip = 0

        if users:
            for user_data in data:
                if not isinstance(user_data, dict):
                    continue
                for user in users:
                    if user_data.get('accountId') == user.jira_user_key:
                        user_data.update({
                            'displayName': user.name
                        })
                        user_updated += 1
        if non_jira_users:
            regex = '^\S+@\S+\.\S+$'
            for user in non_jira_users:
                objs = re.search(regex, user.login)
                if objs:
                    if objs.string == str(user.login):
                        payload = json.dumps({
                            'emailAddress': user.login,
                            'displayName': user.name,
                            'name': user.name,
                            'products': ['jira-software'],
                        })
                        response = requests.post(
                            self.url.rstrip('/') + '/rest/api/3/user', headers=HEADERS,
                            data=payload,
                            auth=(self.user_id_jira, self.api_token),
                            timeout=20)
                        try:
                            response.raise_for_status()
                            data = response.json()
                        except Exception:
                            data = {}
                        if isinstance(data, dict) and data.get('accountId'):
                            user.write({
                                'jira_user_key': data.get('accountId')
                            })
                            user_exported += 1
                else:
                    user_skip += 1

        message = ""
        if user_exported > 0:
            message += _("%d User(s) exported. ", user_exported)
        if user_updated > 0:
            message += _("%d User(s) updated in Jira mapping. ", user_updated)
        if user_exported == 0 and user_updated == 0:
            message = _("Success: There is no new user data to export.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': message,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

    def action_import_users(self):
        try:
            response = requests.get(self.url.rstrip('/') + '/rest/api/2/users/search',
                                    headers=HEADERS,
                                    auth=(self.user_id_jira, self.api_token),
                                    timeout=20)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                _logger.error("Unexpected Jira response (not a list): %s", data)
                data = []
        except Exception as e:
            _logger.error("Failed to fetch users from Jira: %s", e)
            data = []
        user_imported = 0
        user_mapped = 0

        for user_data in data:
            if not isinstance(user_data, dict):
                continue
            users = self.env['res.users'].sudo().search(
                [('login', '=', user_data.get('displayName'))])
            if users:
                users.write({'jira_user_key': user_data.get('accountId')})
                user_mapped += 1
            else:
                self.env['res.users'].create([{
                    'login': user_data.get('emailAddress') or user_data.get('displayName'),
                    'name': user_data.get('displayName'),
                    'jira_user_key': user_data.get('accountId'),
                }])
                user_imported += 1

        message = ""
        if user_imported > 0:
            message += _("%d User(s) imported. ", user_imported)
        if user_mapped > 0:
            message += _("%d User(s) mapped to existing Odoo accounts. ", user_mapped)
        if user_imported == 0 and user_mapped == 0:
            message = _("Success: There is no new user data to import.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': message,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

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
                try:
                    requests.post(attachment_url, headers=ATTACHMENT_HEADERS,
                                  files=attachment_file,
                                  auth=(self.user_id_jira, self.api_token),
                                  timeout=20)
                except Exception as e:
                    _logger.warning("Failed to export attachment %s to Jira: %s", attachment.name, e)

    def _guess_mimetype(self, filename):
        """ Guess the MIME type based on the file extension """
        from mimetypes import guess_type
        mime_type, _ = guess_type(filename)
        return mime_type or 'application/octet-stream'
