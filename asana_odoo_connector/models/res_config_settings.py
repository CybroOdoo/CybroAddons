# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arjun S(odoo@cybrosys.com)
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
from logging import Logger

import requests
from odoo import fields, models, _
from odoo.exceptions import ValidationError

_logger: Logger = logging.getLogger(__name__)
try:
    import asana
    from asana.rest import ApiException
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
    opts = {}
    try:
        section_response = list(api_instance.get_sections_for_project(
            project_gid, opts))
        return section_response
    except ApiException as exc:
        _logger.debug(f"Error while trying to import section {exc}")


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
        if not self.workspace_gid or not self.app_token:
            raise ValidationError(_("Please add App Token and Workspace gid"))
        configuration = asana.Configuration()
        configuration.access_token = self.app_token
        api_client = asana.ApiClient(configuration)
        project_instance = asana.ProjectsApi(api_client)
        opts = {'workspace': self.workspace_gid}
        try:
            project_response = list(project_instance.get_projects(opts))
            split_data = [project_response[project:project + 5] for project in
                          range(0, len(project_response), 10)]
            for project in split_data:
                delay = self.with_delay(priority=1, eta=5)
                delay.create_project(items=project, app_token=self.app_token)
        except ApiException as exc:
            raise ValidationError(
                _('Please check the workspace ID or the app token')) from exc

    def create_project(self, items, app_token):
        """Method create_project to create the project from Asana to Odoo"""
        configuration = asana.Configuration()
        configuration.access_token = app_token
        api_client = asana.ApiClient(configuration)
        for project in items:
            asana_gid = project['gid']
            existing_project = self.env['project.project'].search(
                [('asana_gid', '=', asana_gid)])
            if not existing_project:
                section_data = action_import_project_stages(
                    project_gid=asana_gid,
                    api_client=api_client)
                type_ids = []
                for section in section_data:
                    existing_stage = self.env['project.task.type'].search(
                        [('asana_gid', '=', section['gid'])], limit=1)
                    if existing_stage:
                        type_ids.append((4, existing_stage.id))
                    else:
                        new_stage = self.env['project.task.type'].create({
                            'name': section['name'],
                            'asana_gid': section['gid'],
                        })
                        type_ids.append((0, 0, {'name': new_stage.name,
                                                'asana_gid': new_stage.asana_gid}))
                new_project = self.env['project.project'].create({
                    'name': project['name'],
                    'asana_gid': asana_gid,
                    'type_ids': type_ids
                })
                self.action_import_tasks(
                    api_client=api_client, section_data=section_data,
                    project_id=new_project.id)

    def action_import_tasks(self, api_client, section_data, project_id):
        """
        Method action_import_tasks to import tasks from the asana to odoo
        """
        api_instance = asana.TasksApi(api_client)
        for section in section_data:
            opts = {}
            task_response = list(
                api_instance.get_tasks_for_section(section['gid'], opts))
            for task in task_response:
                self.env['project.task'].create({
                    'name': task['name'],
                    'asana_gid': task['gid'],
                    'stage_id': self.env['project.task.type'].search(
                        [('asana_gid', '=', section['gid'])], limit=1).id,
                    'project_id': project_id
                })
