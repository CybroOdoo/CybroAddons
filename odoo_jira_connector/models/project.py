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
import json
import requests
from requests.auth import HTTPBasicAuth
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Atlassian-Token': 'no-check', 'User-Agent': 'OdooJiraConnector/18.0'}


class ProjectProject(models.Model):
    """Extends project.project to integrate with Jira projects."""
    _inherit = 'project.project'

    project_id_jira = fields.Integer(string='Jira Project ID', readonly=True,
                                     help='Corresponding project id of Jira.')
    jira_project_key = fields.Char(string='Jira Project Key', readonly=True,
                                   help='Corresponding project key of Jira.')
    sprint_active = fields.Boolean(string='Sprint active',
                                   help='To show sprint smart button.')

    @api.model_create_multi
    def create(self, vals_list):
        """Creates projects in Odoo and, if configured, exports them to Jira."""
        self = self.with_context(mail_create_nosubscribe=True)
        projects = super().create(vals_list)
        if self.env['ir.config_parameter'].sudo().get_param('odoo_jira_connector.automatic'):
            jira_connection = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_jira_connector.connection')
            if jira_connection:
                jira_url = self.env['ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.url', False)
                if not jira_url:
                    return projects
                jira_url = jira_url.rstrip('/')
                user = self.env['ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.user_id_jira', False)
                password = self.env['ir.config_parameter'].sudo().get_param(
                    'odoo_jira_connector.api_token', False)
                auth = HTTPBasicAuth(user, password)
                project_headers = {'Accept': 'application/json'}
                try:
                    response = requests.request(
                        'GET', jira_url + '/rest/api/3/project',
                        headers=project_headers, auth=auth,
                        timeout=10)
                    response.raise_for_status()
                    project_json = response.json()
                    name_list = [p['name'] for p in project_json if isinstance(p, dict) and 'name' in p]
                except Exception as e:
                    name_list = []

                for project in projects:
                    # Clean and format project key (must be strictly alphanumeric uppercase)
                    clean_name = "".join(c for c in project.name if c.isalnum()).upper()
                    if len(clean_name) >= 3:
                        project_key = clean_name[:3] + '1' + clean_name[-3:]
                    else:
                        project_key = (clean_name + "PROJ")[:3] + '1' + "PROJ"[-3:]
                    project_keys = project_key.replace(' ', '')
                    
                    project_payload = {
                        'name': project.name, 'key': project_keys,
                        'templateKey': 'com.pyxis.greenhopper.jira:gh-simplified-kanban-classic'
                    }
                    if project.name not in name_list:
                        try:
                            response = requests.request(
                                'POST', jira_url + '/rest/simplified/latest/project',
                                data=json.dumps(project_payload),
                                headers=HEADERS, auth=auth,
                                timeout=10)
                            if response.status_code == 201:
                                data = response.json()
                                if isinstance(data, dict) and 'projectId' in data:
                                    project.write({'project_id_jira': data['projectId'],
                                                   'jira_project_key': data['projectKey']})
                                    import_project_count = self.env['ir.config_parameter'].sudo().get_param('import_project_count')
                                    if import_project_count:
                                        self.env['ir.config_parameter'].sudo().set_param(
                                            'import_project_count', int(import_project_count) + 1)
                            else:
                                data = response.json()
                                if isinstance(data, dict) and 'errors' in data:
                                    if 'projectName' in data['errors']:
                                        raise ValidationError(_("A project with this name already exists. Please rename the project."))
                                    elif 'projectKey' in data['errors']:
                                        raise ValidationError(data['errors']['projectKey'])
                        except (requests.exceptions.RequestException, ValueError) as e:
                            continue
            return projects
        return projects

    def write(self, vals):
        """Updates project details in Odoo and, if configured, in Jira."""
        if self.env['ir.config_parameter'].sudo().get_param('odoo_jira_connector.automatic'):
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
                        "Content-Type": "application/json",
                        "X-Atlassian-Token": "no-check",
                        "User-Agent": "OdooJiraConnector/18.0"
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
                        auth=auth,
                        timeout=10)
                    data = response.json()
                    if 'name' in data:
                        if data['name'] != payload_json['name']:
                            requests.request(
                                "PUT",
                                url, data=payload, headers=headers, auth=auth,
                                timeout=10)
                    else:
                        requests.request(
                            "PUT",
                            url, data=payload, headers=headers, auth=auth,
                            timeout=10)
        return super(ProjectProject, self).write(vals)

    def action_get_sprint(self):
        """Returns an action to view sprints associated with the project."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sprints',
            'view_mode': 'list,form',
            'res_model': 'jira.sprint',
            'context': {'default_project_id': self.id},
            'domain': [('project_id', '=', self.id)],
        }
