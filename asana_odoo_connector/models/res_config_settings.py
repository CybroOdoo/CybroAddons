# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################
import logging
import requests
from odoo import fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
try:
    import asana
except ImportError:
    _logger.debug('Cannot `import asana`.')


def action_notify(success):
    """
    Method action_notify used to notify whether the connection to the asana is
    successful or not.
    """
    notification = {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': _('Connection successful!') if success is True else _(
                'Connection not successful!'),
            'message': 'Connection to Asana is successful.' if success is True else 'Connection to Asana is not successful.',
            'sticky': True,
            'type': 'success' if success is True else 'danger'
        }
    }
    return notification


def action_import_project_stages(project_gid, api_client):
    """
    Method action_import_project_stages used to import the project stages from
    asana to odoo
    """
    api_instance = asana.SectionsApi(api_client)
    section_response = api_instance.get_sections_for_project(
        project_gid)
    return section_response


class ResConfigSettings(models.TransientModel):
    """
    Inherits the model Res Config Settings to add extra fields and
    functionalities to this model
    """
    _inherit = 'res.config.settings'

    workspace_gid = fields.Char(string='Workspace ID',
                                help='ID of the workspace in asana',
                                config_parameter='asana_odoo_connector.workspace_gid')
    app_token = fields.Char(string='App Token',
                            help='Personal Access Token of the corresponding '
                                 'asana account',
                            config_parameter='asana_odoo_connector.app_token')

    def action_test_asana(self):
        """
        Method action_test_asana to test the connection from odoo to asana
        """
        workspace_gid = self.workspace_gid
        api_endpoint = f'https://app.asana.com/api/1.0/workspaces/{workspace_gid}'
        access_token = self.app_token
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        response = requests.get(api_endpoint, headers=headers, timeout=10)
        if response.status_code == 200:
            success = True
            notification = action_notify(success)
            self.env['ir.config_parameter'].sudo().set_param(
                'asana_odoo_connector.connection_successful', True)
            return notification
        success = False
        notification = action_notify(success)
        return notification

    def action_import_projects(self):
        """
        Method action_import_projects to import the project from asana to odoo
        """
        configuration = asana.Configuration()
        configuration.access_token = self.app_token
        api_client = asana.ApiClient(configuration)
        project_instance = asana.ProjectsApi(api_client)
        section_instance = asana.SectionsApi(api_client)
        workspace = self.workspace_gid
        opts = {
            'workspace': workspace
        }
        try:
            project_response = project_instance.get_projects(opts)
            for project in project_response:
                asana_gid = project['gid']
                existing_project = self.env['project.project'].search(
                    [('asana_gid', '=', asana_gid)])
                if not existing_project:
                    opts = {}
                    section_data = section_instance.get_sections_for_project(
                        asana_gid, opts)
                    type_ids = [
                        (0, 0, {'name': section['name'],
                                'asana_gid': section['gid']})
                        for section in section_data]
                    new_project = self.env['project.project'].create({
                        'name': project['name'],
                        'asana_gid': asana_gid,
                        'type_ids': type_ids
                    })
                    self.action_import_tasks(
                        api_client=api_client,
                        project_id=new_project.id,
                        asana_gid= asana_gid)
                else:
                    self.action_import_tasks(
                        api_client=api_client,
                        project_id=existing_project.id,
                        asana_gid=asana_gid)
        except Exception as exc:
            raise ValidationError(
                _('Please check the workspace ID or the app token')) from exc

    def action_import_tasks(self, api_client, project_id, asana_gid):
        """
        Method action_import_tasks to import tasks from the asana to odoo
        """
        api_instance = asana.TasksApi(api_client)
        section_instance = asana.SectionsApi(api_client)
        opts = {}
        section_data = section_instance.get_sections_for_project(asana_gid,
                                                                 opts)
        for section in section_data:
            opts ={}
            task_response = api_instance.get_tasks_for_section(section['gid'],
                                                               opts)
            for task in task_response:
                existing_task = self.env['project.task'].search(
                    [('asana_gid', '=', task['gid']),
                     ('project_id', '=', project_id)])
                if not existing_task:
                    self.env['project.task'].create({
                        'name': task['name'],
                        'project_id': project_id,
                        'asana_gid': task['gid'],
                        'stage_id': self.env['project.task.type'].search(
                            [('asana_gid', '=', section['gid']),
                             ('project_ids', '=', project_id)]).id,
                    })
