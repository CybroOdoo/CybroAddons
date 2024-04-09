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
from odoo import fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
try:
    import asana
    from asana.rest import ApiException
except ImportError:
    _logger.debug('Cannot `import asana`.')


class ProjectProject(models.Model):
    """
    Inherits the model project.project to add extra fields and functionalities
    for the working of the odoo to asana import and export.
    """
    _inherit = 'project.project'

    asana_gid = fields.Char(string='Asana GID',
                            help='Asana ID for the project record',
                            readonly=True)

    def action_export_to_asana(self):
        """
        Method action_export_to_asana used to export the data in the odoo to
        asana
        """
        workspace_gid = self.env[
            'ir.config_parameter'].sudo().get_param(
            'asana_odoo_connector.workspace_gid')
        if not workspace_gid or not self.env[
            'ir.config_parameter'].sudo().get_param(
            'asana_odoo_connector.app_token'):
            raise ValidationError(_("Add Configurations"))
        try:
            batch_size = 5  # Specify the batch size
            start_index = 0
            while start_index < len(self):
                exported_project = self.filtered(
                    lambda self: not self.asana_gid)
                project_batch = exported_project[
                                start_index:start_index + batch_size]
                delay = self.with_delay(priority=1, eta=5)
                delay.export_project(items=project_batch,
                                     workspace_gid=workspace_gid)
                start_index += batch_size
        except ApiException as exc:
            raise ValidationError(
                _('Please check the workspace ID or the app token')) from exc

    def export_project(self, items, workspace_gid):
        """Method export_project to export the data from Odoo to Asana"""
        configuration = asana.Configuration()
        app_token = self.env[
            'ir.config_parameter'].sudo().get_param(
            'asana_odoo_connector.app_token')
        configuration.access_token = app_token
        api_client = asana.ApiClient(configuration)
        project_instance = asana.ProjectsApi(api_client)
        for project in items:
            project_body = {
                "data": {
                    "name": project.name
                }
            }
            opts = {}
            project_response = project_instance.create_project_for_workspace(
                project_body, workspace_gid, opts)
            project.asana_gid = project_response['gid']
            project_gid = project_response['gid']
            task_instance = asana.TasksApi(api_client)
            section_instance = asana.SectionsApi(api_client)
            for section in project.type_ids:
                opts = {
                    "body": {
                        "data": {
                            "name": section.name,
                        }
                    }
                }
                section_responses = section_instance.create_section_for_project(
                    project_gid, opts
                )
                section.asana_gid = section_responses['gid']
            for task in project.tasks:
                body = {
                    "data":
                        {
                            'name': task.name,
                            'workspace': workspace_gid,
                            "projects": project_gid,
                            "memberships": [
                                {
                                    'project': project_gid,
                                    'section': task.stage_id.asana_gid
                                }
                            ]}
                }
                opts = {}
                task_instance.create_task(body, opts)
