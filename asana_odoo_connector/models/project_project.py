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
from odoo import fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)
try:
    import asana
except ImportError:
    _logger.debug('Cannot `import asana`.')


class ProjectProject(models.Model):
    """Inherits project.project to enable exporting to Asana."""
    _inherit = 'project.project'

    asana_gid = fields.Char(
        string='Asana GID',
        help='Asana ID for the project record',
        readonly=True,
    )

    def action_export_to_asana(self):
        """Export selected projects and their stages/tasks to Asana."""
        params = self.env['ir.config_parameter'].sudo()
        app_token = params.get_str('asana_odoo_connector.app_token')
        workspace_gid = params.get_str('asana_odoo_connector.workspace_gid')
        if not app_token or not workspace_gid:
            raise UserError(
                _('Please configure the Workspace ID and App Token in '
                  'Asana settings before exporting.')
            )

        configuration = asana.Configuration()
        configuration.access_token = app_token
        api_client = asana.ApiClient(configuration)
        project_instance = asana.ProjectsApi(api_client)
        try:
            for project in self:
                if not project.asana_gid:
                    project_body = {"data": {"name": project.name}}
                    project_response = (
                        project_instance.create_project_for_workspace(
                            project_body, workspace_gid, {}
                        )
                    )
                    project.asana_gid = project_response['gid']
                    project_gid = project_response['gid']
                    task_instance = asana.TasksApi(api_client)
                    section_instance = asana.SectionsApi(api_client)
                    stage_section_map = {}
                    for section in project.type_ids:
                        opts = {
                            'body': {"data": {'name': section.name}}
                        }
                        section_resp = (
                            section_instance.create_section_for_project(
                                project_gid, opts
                            )
                        )
                        sec_gid = section_resp['gid']
                        stage_section_map[section.id] = sec_gid
                        if not section.asana_gid:
                            section.asana_gid = sec_gid
                    for task in project.tasks:
                        section_gid = (
                            stage_section_map.get(task.stage_id.id)
                            if task.stage_id else False
                        )
                        memberships = [{'project': project_gid}]
                        if section_gid:
                            memberships[0]['section'] = section_gid
                        body = {
                            "data": {
                                'name': task.name,
                                'workspace': workspace_gid,
                                "projects": [project_gid],
                                "memberships": memberships,
                            }
                        }
                        task_resp = task_instance.create_task(body, {})
                        if task_resp and 'gid' in task_resp:
                            task.asana_gid = task_resp['gid']
        except UserError:
            raise
        except Exception as exc:
            raise ValidationError(
                _('Please check the workspace ID or the app token')
            ) from exc
