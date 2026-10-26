# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com/>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import logging
import requests
from odoo import Command, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)
try:
    import asana
except ImportError:
    _logger.debug('Cannot `import asana`.')


class ResConfigSettings(models.TransientModel):
    """Inherits res.config.settings to add Asana integration settings."""
    _inherit = 'res.config.settings'

    workspace_gid = fields.Char(
        string='Workspace ID',
        help='ID of the workspace in Asana',
        config_parameter='asana_odoo_connector.workspace_gid',
    )
    app_token = fields.Char(
        string='App Token',
        help='Personal Access Token of the corresponding Asana account',
        config_parameter='asana_odoo_connector.app_token',
    )

    def _action_notify(self, success):
        """Notify whether the connection to Asana is successful."""
        title = _('Connection successful!') if success else _(
            'Connection not successful!'
        )
        message = _('Connection to Asana is successful.') if success else _(
            'Connection to Asana is not successful.'
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'sticky': True,
                'type': 'success' if success else 'danger',
            },
        }

    def action_test_asana(self):
        """Test the connection from Odoo to Asana."""
        params = self.env['ir.config_parameter'].sudo()
        workspace_gid = self.workspace_gid or params.get_str(
            'asana_odoo_connector.workspace_gid'
        )
        access_token = self.app_token or params.get_str(
            'asana_odoo_connector.app_token'
        )
        if not workspace_gid or not access_token:
            return self._action_notify(False)
        api_endpoint = (
            f'https://app.asana.com/api/1.0/workspaces/{workspace_gid}'
        )
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        try:
            response = requests.get(api_endpoint, headers=headers, timeout=10)
            if response.status_code == 200:
                params.set_bool(
                    'asana_odoo_connector.connection_successful', True
                )
                return self._action_notify(True)
        except Exception as exc:
            _logger.warning("Failed to connect to Asana: %s", exc)
        return self._action_notify(False)

    def action_import_projects(self):
        """Import projects and tasks from Asana to Odoo."""
        params = self.env['ir.config_parameter'].sudo()
        app_token = self.app_token or params.get_str(
            'asana_odoo_connector.app_token'
        )
        workspace = self.workspace_gid or params.get_str(
            'asana_odoo_connector.workspace_gid'
        )
        if not app_token or not workspace:
            raise UserError(
                _('Please configure the Workspace ID and App Token in '
                  'Asana settings before importing.')
            )
        configuration = asana.Configuration()
        configuration.access_token = app_token
        api_client = asana.ApiClient(configuration)
        project_instance = asana.ProjectsApi(api_client)
        section_instance = asana.SectionsApi(api_client)
        opts = {'workspace': workspace}
        try:
            project_response = project_instance.get_projects(opts)
            for project in project_response:
                asana_gid = project['gid']
                existing_project = self.env['project.project'].search(
                    [('asana_gid', '=', asana_gid)], limit=1
                )
                if not existing_project:
                    section_data = section_instance.get_sections_for_project(
                        asana_gid, {}
                    )
                    type_ids = [
                        Command.create({
                            'name': section['name'],
                            'asana_gid': section['gid'],
                        })
                        for section in section_data
                    ]
                    new_project = self.env['project.project'].create({
                        'name': project['name'],
                        'asana_gid': asana_gid,
                        'type_ids': type_ids,
                    })
                    self.action_import_tasks(
                        api_client=api_client,
                        project_id=new_project.id,
                        asana_gid=asana_gid,
                    )
                else:
                    self.action_import_tasks(
                        api_client=api_client,
                        project_id=existing_project.id,
                        asana_gid=asana_gid,
                    )
        except UserError:
            raise
        except Exception as exc:
            raise ValidationError(
                _('Please check the workspace ID or the app token')
            ) from exc

    def action_import_tasks(self, api_client, project_id, asana_gid):
        """Import tasks from Asana to Odoo."""
        api_instance = asana.TasksApi(api_client)
        section_instance = asana.SectionsApi(api_client)
        section_data = section_instance.get_sections_for_project(
            asana_gid, {}
        )
        for section in section_data:
            task_response = api_instance.get_tasks_for_section(
                section['gid'], {}
            )
            stage = self.env['project.task.type'].search(
                [('asana_gid', '=', section['gid']),
                 ('project_ids', '=', project_id)], limit=1
            )
            for task in task_response:
                existing_task = self.env['project.task'].search(
                    [('asana_gid', '=', task['gid']),
                     ('project_id', '=', project_id)], limit=1
                )
                if not existing_task:
                    self.env['project.task'].create({
                        'name': task['name'],
                        'project_id': project_id,
                        'asana_gid': task['gid'],
                        'stage_id': stage.id if stage else False,
                    })
