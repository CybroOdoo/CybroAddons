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
from requests.auth import HTTPBasicAuth
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# The Header parameters
HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json'}


class ProjectProject(models.Model):
    """
    This class is inherited for adding some extra field and override the
    create and write function also to add function to show sprint
    Methods:
        create(vals_list):
            extends create() to export project to Jira
        write(vals):
            extends write() to update corresponding project in Jira
    """
    _inherit = 'project.project'

    project_id_jira = fields.Integer(string='Jira Project ID',
                                     help='Corresponding project id of Jira.',
                                     readonly=True)
    jira_project_key = fields.Char(string='Jira Project Key',
                                   help='Corresponding project key of Jira.',
                                   readonly=True)
    sprint_active = fields.Boolean(string='Sprint active',
                                   help='To show sprint smart button.')
    board_id_jira = fields.Integer(string='Jira Board ID',
                                   help='Corresponding Board id of Jira.',
                                   readonly=True)

    def action_get_sprint(self):
        """Getting sprint inside the project"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sprints',
            'view_mode': 'tree,form',
            'res_model': 'jira.sprint',
            'context': {'default_project_id': self.id},
            'domain': [('project_id', '=', self.id)],
        }

    @api.model_create_multi
    def create(self, vals_list):
        """ Overrides create method of project to export project to Jira """
        self = self.with_context(mail_create_nosubscribe=True)
        projects = super().create(vals_list)
        jira_connection = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_jira_connector.connection')
        if jira_connection:
            jira_url = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.url', False)
            user = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.user_id_jira', False)
            password = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.api_token', False)
            auth = HTTPBasicAuth(user, password)
            project_headers = {'Accept': 'application/json'}
            response = requests.request(
                'GET', jira_url + '/rest/api/3/project/',
                headers=project_headers, auth=auth)
            projects_json = json.dumps(
                json.loads(response.text), sort_keys=True, indent=4,
                separators=(',', ': '))
            project_json = json.loads(projects_json)
            name_list = [project['name'] for project in project_json]
            key = projects.name.upper()
            project_key = key[:3] + '1' + key[-3:]
            project_keys = project_key.replace(' ', '')
            auth = HTTPBasicAuth(user, password)
            project_payload = {
                'name': projects.name, 'key': project_keys,
                'templateKey': 'com.pyxis.greenhopper.jira:gh-simplified'
                               '-kanban-classic'
            }
            if projects.name not in name_list:
                response = requests.request(
                    'POST', jira_url + 'rest/simplified/latest/project',
                    data=json.dumps(project_payload),
                    headers=HEADERS, auth=auth)
                data = response.json()
                if 'projectId' in data:
                    projects.write({'project_id_jira': data['projectId'],
                                    'jira_project_key': data['projectKey']})
                    self.env['ir.config_parameter'].sudo().set_param(
                        'import_project_count', int(
                            self.env['ir.config_parameter'].sudo().get_param(
                                'import_project_count')) + 1)
                elif 'errors' in data and 'projectName' in data['errors']:
                    raise ValidationError(
                        "A project with this name already exists. Please "
                        "rename the project.")
                elif 'errors' in data and 'projectKey' in data['errors']:
                    raise ValidationError(data['errors']['projectKey'])
        return projects

    def write(self, vals):
        """ Overrides the write method of project.project to update project
        name in Jira when we update the project in Odoo"""

        jira_connection = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_jira_connector.connection')
        if jira_connection:
            for project in self:
                jira_url = self.env['ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.url')
                user = self.env['ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.user_id_jira')
                password = self.env['ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.api_token')
                auth = (user, password)
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
                url = (f"{jira_url}/rest/api/3/project/"
                       f"{project.jira_project_key}")
                payload = json.dumps({
                    "name": vals.get('name'),
                })
                payload_json = json.loads(payload)
                response = requests.get(
                    url,
                    headers=headers,
                    auth=auth)
                data = response.json()
                if 'name' in data:
                    if data['name'] != payload_json['name']:
                        requests.request(
                            "PUT",
                            url, data=payload, headers=headers, auth=auth)
                else:
                    requests.request(
                        "PUT",
                        url, data=payload, headers=headers, auth=auth)
            return super(ProjectProject, self).write(vals)
