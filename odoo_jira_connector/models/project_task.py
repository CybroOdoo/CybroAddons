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
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from odoo import api, fields, models, _
from odoo.tools import html2plaintext

# The Header parameters
HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json'}


class ProjectTask(models.Model):
    """
    This class is inherited for adding some extra field and override the
        create function
        Methods:
            create(vals_list):
                extends create() to export tasks to Jira
            unlink():
                extends unlink() to delete a task in Jira when we delete the
                task in Odoo
            write(vals):
                extends write() to update a task in Jira when we update the
                task in Odoo
    """
    _inherit = 'project.task'

    task_id_jira = fields.Char(string='Jira Task ID', help='Task id of Jira.',
                               readonly=True)
    sprint_id = fields.Many2one('jira.sprint',
                                help="Sprint of this task.", readonly=True)
    task_sprint_active = fields.Boolean(string="Active Sprint",
                                        compute="_compute_task_sprint_active",
                                        store=True,
                                        help="Boolean field to check whether "
                                             "the sprint is active or not.")

    @api.depends('project_id.sprint_active')
    def _compute_task_sprint_active(self):
        """compute function to make sprint_id invisible by changing
        'task_sprint_active' field to true"""
        for rec in self:
            if rec.project_id.sprint_active:
                rec.task_sprint_active = True

    @api.model
    def create(self, vals_list):
        """ Override the create method of tasks to export tasks to Jira """
        res = super(ProjectTask, self).create(vals_list)
        jira_connection = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_jira_connector.connection')
        if jira_connection:
            jira_url = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.url')
            user = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.user_id_jira')
            password = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.api_token')
            query = {'jql': 'project = %s' % res.project_id.jira_project_key}
            requests.get(jira_url + 'rest/api/3/search', headers=HEADERS,
                         params=query, auth=(user, password))
            if not res.task_id_jira:
                payload = json.dumps({
                    'fields': {
                        'project': {'key': res.project_id.jira_project_key},
                        'summary': res.name,
                        'description': res.description,
                        'issuetype': {'name': 'Task'}
                    }
                })
                response = requests.post(
                    jira_url + '/rest/api/2/issue', headers=HEADERS,
                    data=payload, auth=(user, password))
                data = response.json()
                res.task_id_jira = str(data.get('key'))
                self.env['ir.config_parameter'].sudo().set_param(
                    'export_task_count', int(
                        self.env['ir.config_parameter'].sudo().get_param(
                            'export_task_count')) + 1)
        return res

    def unlink(self):
        """ Overrides the unlink method of task to delete a task in Jira when
        we delete the task in Odoo """
        for task in self:
            if task.stage_id and task.stage_id.fold:
                raise Warning(_('You cannot delete a task in a folded stage.'))
            jira_connection = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.connection')
            if jira_connection:
                jira_url = self.env['ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.url', '')
                user = self.env['ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.user_id_jira')
                password = self.env['ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.api_token')
                if task.task_id_jira:
                    requests.delete(
                        jira_url + '/rest/api/3/issue/' + task.task_id_jira,
                        headers=HEADERS, auth=(user, password))
        return super(ProjectTask, self).unlink()

    def write(self, vals):
        """ Overrides the write method of task to update a task's name in
        Jira when we update the task in Odoo"""
        jira_connection = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_jira_connector.connection')

        if jira_connection:
            jira_url = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.url', '')
            user = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.user_id_jira')
            password = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.api_token')

            for task in self:
                if task.task_id_jira and 'name' in vals:
                    new_task_name = vals['name']
                    payload = {
                        "fields": {
                            "summary": new_task_name
                        }
                    }
                    requests.put(
                        jira_url + '/rest/api/3/issue/' + task.task_id_jira,
                        json=payload, headers=HEADERS, auth=(user, password))
        return super(ProjectTask, self).write(vals)

    def webhook_data_handle(self, jira_data, webhook_event):
        """Function to Handle Jira Data Received from Webhook"""
        if webhook_event == 'project_created':
            self.create_project(jira_data)
        elif webhook_event == 'project_updated':
            self.update_project(jira_data)
        elif webhook_event == 'project_soft_deleted':
            self.delete_project(jira_data)
        elif webhook_event == 'jira:issue_created':
            self.create_task(jira_data)
        elif webhook_event == 'jira:issue_deleted':
            self.delete_task(jira_data)
        elif webhook_event == 'comment_created':
            self.create_comment(jira_data)
        elif webhook_event == 'comment_deleted':
            self.delete_comment(jira_data)
        elif webhook_event == 'user_created':
            self.create_user(jira_data)
        elif webhook_event == 'user_deleted':
            self.delete_user(jira_data)
        elif webhook_event == 'board_configuration_changed':
            self.board_configuration_change(jira_data)
        elif webhook_event == 'jira:issue_updated':
            self.update_task(jira_data)
        elif webhook_event == 'attachment_deleted':
            self.delete_attachment(jira_data)
        elif webhook_event == 'sprint_started':
            self.sprint_started(jira_data)
        elif webhook_event == 'sprint_closed':
            self.sprint_closed(jira_data)

    def create_project(self, jira_data):
        """function to create project based on webhook response"""
        jira_project = jira_data['project']
        existing_project = self.env['project.project'].sudo().search(
            [('project_id_jira', '=', jira_project['id'])])
        values = {
            'name': jira_project['name'],
            'project_id_jira': jira_project['id'],
            'jira_project_key': jira_project['key']
        }
        if not existing_project:
            imported_project = self.env['project.project'].sudo().create(
                values)
            url = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.url')
            user = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.user_id_jira')
            password = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.api_token')
            auth = HTTPBasicAuth(user, password)
            headers = {
                "Accept": "application/json"
            }
            response = requests.request(
                "GET",
                url + "/rest/api/3/project/" + jira_project['key'],
                headers=headers,
                auth=auth
            )
            data = response.json()
            style_value = data.get('style')
            if style_value == 'classic':
                imported_project.write({'sprint_active': False})
            else:
                imported_project.write({'sprint_active': True})

    def update_project(self, jira_data):
        """function to update project based on webhook response"""
        project_id = jira_data['project']['id']
        existing_project = self.env['project.project'].sudo().search(
            [('project_id_jira', '=', project_id)])
        if existing_project.name != jira_data['project']['name']:
            existing_project.write({'name': jira_data['project']['name']})

    def delete_project(self, jira_data):
        """function to delete project based on webhook response"""
        project_id = (jira_data['project']['id'])
        self.env['project.project'].sudo().search(
            [('project_id_jira', '=', project_id)]).unlink()

    def create_task(self, jira_data):
        """function to create task based on webhook response"""
        task_name = jira_data['issue']['fields']['summary']
        task_key = jira_data['issue']['key']
        jira_project_id = jira_data['issue']['fields']['project']['id']
        project = self.env['project.project'].sudo().search(
            [('project_id_jira', '=', int(jira_project_id))])
        existing_task = self.env['project.task'].sudo().search(
            [('task_id_jira', '=', jira_data['issue']['key'])])
        if not existing_task:
            self.env['project.task'].sudo().create({
                'project_id': project.id,
                'name': task_name,
                'task_id_jira': task_key
            })

    def delete_task(self, jira_data):
        """function to delete task based on webhook response"""
        task_key = jira_data['issue']['key']
        self.env['project.task'].sudo().search(
            [('task_id_jira', '=', task_key)]).unlink()

    def create_comment(self, jira_data):
        """function to create comment based on webhook response"""
        text = jira_data['comment']['body']
        task_key = jira_data['issue']['key']
        task = self.env['project.task'].sudo().search(
            [('task_id_jira', '=', task_key)])
        existing_message = self.env['mail.message'].sudo().search(
            ['&', ('res_id', '=', task.id),
             ('model', '=', 'project.task'),
             ('message_id_jira', '=', jira_data['comment']['id'])])
        if not existing_message:
            input_string = str(text)
            parts = input_string.split(".")
            if len(parts) > 1:
                body = parts[1]
            else:
                body = parts[0]
            self.env['mail.message'].sudo().create(
                {"body": html2plaintext(body),
                 'model': 'project.task',
                 'res_id': task.id,
                 'message_id_jira': jira_data['comment']['id']
                 })

    def delete_comment(self, jira_data):
        """function to delete comment based on webhook response"""
        self.env['mail.message'].sudo().search(
            [('message_id_jira', '=',
              jira_data['comment']['id'])]).unlink()

    def create_user(self, jira_data):
        """function to create user based on webhook response"""
        existing_user = self.env['res.users']. \
            search([('jira_user_key', '=', jira_data['user']['accountId'])])
        if not existing_user:
            self.env['res.users'].sudo().create({
                'login': jira_data['user']['displayName'],
                'name': jira_data['user']['displayName'],
                'jira_user_key': jira_data['user']['accountId']
            })

    def delete_user(self, jira_data):
        """function to delete user based on webhook response"""
        self.env['res.users'].sudo().search(
            [('jira_user_key', '=', jira_data['accountId'])]).unlink()

    def board_configuration_change(self, jira_data):
        """function to create stages or write project into stages based on
        webhook response"""
        columns = jira_data['configuration']['columnConfig']['columns']
        if jira_data['configuration'].get('location'):
            project_key = jira_data['configuration']['location']['key']
            project = self.env['project.project'].sudo().search(
                [('jira_project_key', '=', project_key)])
            sequence_value = 1
            for column in columns:
                if column['name'] != 'Backlog':
                    stages_jira_id = column['statuses'][0]['id']
                    existing_stage = self.env[
                        'project.task.type'].sudo().search(
                        [('stages_jira_id', '=', stages_jira_id)])
                    existing_stage.write({'project_ids': project,
                                          'sequence': sequence_value})
                    if not existing_stage:
                        values = {
                            'name': column['name'],
                            'stages_jira_id': stages_jira_id,
                            'jira_project_key': project_key,
                            'project_ids': project,
                            'sequence': sequence_value,
                        }
                        self.env['project.task.type'].sudo().create(
                            values)
                    sequence_value += 1
            project.write({'board_id_jira': jira_data['configuration']['id']})
        else:
            board_id_jira = jira_data['configuration']['id']
            project = self.env['project.project'].search(
                [('board_id_jira', '=', board_id_jira)])
            existing_stages = self.env[
                'project.task.type'].sudo().search(
                [('project_ids', 'in', project.id),
                 ('stages_jira_id', '!=', '0')])
            jira_status_ids = []
            for column in columns:
                for status in column['statuses']:
                    jira_status_ids.append(status['id'])
            if len(jira_status_ids) < len(existing_stages.ids):
                removed_stage = self.env[
                    'project.task.type'].sudo().search(
                    [('project_ids', 'in', project.id),
                     ('stages_jira_id', 'not in', jira_status_ids)])
                removed_stage.unlink()
            elif len(jira_status_ids) > len(existing_stages.ids):
                columns = jira_data['configuration']['columnConfig'][
                    'columns']
                num_stages = len(columns)
                stage_id = columns[num_stages - 1]['statuses'][0]['id']
                values = {
                    'name': columns[num_stages - 1]['name'],
                    'stages_jira_id': stage_id,
                    'project_ids': project,
                    'sequence': num_stages,
                }
                self.env['project.task.type'].sudo().create(values)

    def update_task(self, jira_data):
        """function to update a task, which includes changing the task stage,
         adding attachments, adding a description to the task,
         changing the task's name,
         and adding a sprint based on webhook response"""
        task_key = jira_data['issue']['key']
        imported_task = self.env['project.task'].sudo().search(
            [('task_id_jira', '=', task_key)])
        to_value = jira_data['changelog']['items'][0]['to']
        if jira_data['changelog']['items'][0]['field'] == 'resolution':
            second_to_value = jira_data['changelog']['items'][1]['to']
            task_stage = self.env['project.task.type'].sudo().search(
                [('stages_jira_id', '=', second_to_value)])
            imported_task.write({'stage_id': task_stage.id})
        elif jira_data['changelog']['items'][0]['field'] == 'status':
            task_stage = self.env['project.task.type'].sudo().search(
                [('stages_jira_id', '=', to_value)])
            imported_task.write({'stage_id': task_stage.id})
        elif jira_data['changelog']['items'][0]['field'] == 'Attachment':
            if jira_data['changelog']['items'][0]['to'] != 'None':
                attachments = jira_data["issue"]['fields']['attachment']
                jira_attachment_id = [attachment['id'] for attachment in
                                      attachments]
                num_attachments = len(jira_attachment_id)
                user_name = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.user_id_jira')
                api_token = self.env[
                    'ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.api_token')
                auth = HTTPBasicAuth(user_name, api_token)
                if num_attachments > 0:
                    name = attachments[num_attachments - 1].get('filename')
                    mime_type = attachments[num_attachments - 1].get(
                        'mimeType')
                    src = attachments[num_attachments - 1].get('content')
                    jira_id = attachments[num_attachments - 1].get('id')
                    image = base64.b64encode(
                        requests.get(src, auth=auth).content)
                    existing_attachments = self.env[
                        'ir.attachment'].sudo().search(
                        [('res_id', '=', imported_task.id),
                         ('res_model', '=', 'project.task'),
                         ('attachment_id_jira', '=', jira_id)]
                    )
                    values = {
                        'name': name,
                        'type': 'binary',
                        'datas': image,
                        'res_model': 'project.task',
                        'res_id': imported_task.id,
                        'mimetype': mime_type,
                        'attachment_id_jira': jira_id
                    }
                    if not existing_attachments:
                        self.env['ir.attachment'].sudo().create(values)
                else:
                    pass
        elif jira_data['changelog']['items'][0]['field'] == 'description':
            imported_task.update({'description': jira_data['changelog']
            ['items'][0]['toString']})
        elif jira_data['changelog']['items'][0]['field'] == 'summary':
            if imported_task.name != jira_data['changelog']['items'][0] \
                    ['toString']:
                imported_task.write(
                    {'name': jira_data['changelog']['items'][0]
                    ['toString']})
        elif jira_data['changelog']['items'][0]['field'] == 'Sprint':
            project_key = jira_data['issue']['fields']['project']['key']
            project = self.env['project.project'].sudo().search(
                [('jira_project_key', '=', project_key)])
            custom_field = jira_data['issue']['fields']['customfield_10020']
            if len(custom_field) > 1:
                jira_sprint = self.env['jira.sprint'].sudo().search(
                    [('sprint_id_jira', '=',
                      custom_field[len(custom_field) - 1]['id'])])
                if not jira_sprint:
                    vals = {
                        'name': custom_field[len(custom_field) - 1]['name'],
                        'sprint_id_jira':
                            custom_field[len(custom_field) - 1]['id'],
                        'project_id': project.id
                    }
                    sprint = self.env['jira.sprint'].sudo().create(vals)
                    if project.task_ids:
                        for rec in project.task_ids:
                            rec.write({'sprint_id': sprint.id})
            else:
                jira_sprint = self.env['jira.sprint'].sudo().search([(
                    'sprint_id_jira', '=', custom_field[0]['id'])])
                if not jira_sprint:
                    vals = {
                        'name': custom_field[0]['name'],
                        'sprint_id_jira': custom_field[0]['id'],
                        'project_id': project.id
                    }
                    sprint = self.env['jira.sprint'].sudo().create(vals)
                    if project.task_ids:
                        for rec in project.task_ids:
                            rec.write({'sprint_id': sprint.id})
                            if rec.task_id_jira != task_key:
                                self.create({
                                    'project_id': project.id,
                                    'name': jira_data['issue']['fields'][
                                        'summary'],
                                    'task_id_jira': task_key,
                                    'sprint_id': jira_sprint.id
                                })
                                break
                    else:
                        task_name = jira_data['issue']['fields']['summary']
                        self.create({
                            'project_id': project.id,
                            'name': task_name,
                            'task_id_jira': task_key,
                            'sprint_id': sprint.id
                        })
                else:
                    if project.task_ids:
                        for rec in project.task_ids:
                            rec.write({'sprint_id': jira_sprint.id})
                            if rec.task_id_jira != task_key:
                                self.create({
                                    'project_id': project.id,
                                    'name': jira_data['issue']['fields'][
                                        'summary'],
                                    'task_id_jira': task_key,
                                    'sprint_id': jira_sprint.id
                                })
                                break
                    else:
                        task_name = jira_data['issue']['fields']['summary']
                        self.create({
                            'project_id': project.id,
                            'name': task_name,
                            'task_id_jira': task_key,
                            'sprint_id': jira_sprint.id
                        })

    def delete_attachment(self, jira_data):
        """function to delete attachment based on the response received from
         webhook"""
        jira_id = jira_data['attachment']['id']
        self.env['ir.attachment'].sudo().search(
            [('attachment_id_jira', '=', jira_id)]).unlink()

    def sprint_started(self, jira_data):
        """function to start sprint which is created using webhook response"""
        sprint_in_odoo = self.env['jira.sprint'].sudo().search(
            [('sprint_id_jira', '=', jira_data['sprint']['id'])])
        if sprint_in_odoo:
            start_date = jira_data['sprint']['startDate']
            input_start_date = datetime. \
                strptime(start_date, '%Y-%m-%dT%H:%M:%S.%fZ')
            jira_start_date = input_start_date.strftime(
                '%Y-%m-%d %H:%M:%S')
            end_date = jira_data['sprint']['endDate']
            input_end_date = datetime. \
                strptime(end_date, '%Y-%m-%dT%H:%M:%S.%fZ')
            jira_end_date = input_end_date.strftime(
                '%Y-%m-%d %H:%M:%S')
            sprint_in_odoo.write({
                'start_date': jira_start_date,
                'end_date': jira_end_date,
                'sprint_goal': jira_data['sprint']['goal'],
                'state': 'ongoing'
            })

    def sprint_closed(self, jira_data):
        """function to close sprint which is created using webhook response"""
        sprint_in_odoo = self.env['jira.sprint'].sudo().search(
            [('sprint_id_jira', '=', jira_data['sprint']['id'])])
        if sprint_in_odoo:
            sprint_in_odoo.write({'state': 'completed'})
            self.env['project.task'].sudo().search(
                [('stage_id.name', '=', 'Done'),
                 ('sprint_id', '=', sprint_in_odoo.id)]).unlink()
