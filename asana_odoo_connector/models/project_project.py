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
from odoo import fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
try:
    import asana
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
        configuration = asana.Configuration()
        configuration.access_token = self.env[
            'ir.config_parameter'].sudo().get_param(
            'asana_odoo_connector.app_token')
        api_client = asana.ApiClient(configuration)
        project_instance = asana.ProjectsApi(api_client)
        workspace_gid = self.env[
            'ir.config_parameter'].sudo().get_param(
            'asana_odoo_connector.workspace_gid')
        try:
            for project in self:
                if not project.asana_gid:
                    project_body = {"data":{"name": project.name}}
                    project_response = project_instance.create_project_for_workspace(
                        project_body, workspace_gid, {})
                    project.asana_gid = project_response['gid']
                    project_gid = project_response['gid']
                    task_instance = asana.TasksApi(api_client)
                    section_instance = asana.SectionsApi(api_client)
                    for section in project.type_ids:
                        opts = {
                            'body': {"data": {'name': section.name}}
                        }
                        section_responses = section_instance.create_section_for_project(
                            project_gid, opts
                        )
                        section.asana_gid = section_responses['gid']
                    for task in project.tasks:
                        body = {"data": {'name': task.name,
                                         'workspace': workspace_gid,
                                         "projects": project_gid,
                                         "memberships": [{
                                             'project': project_gid,
                                             'section': task.stage_id.asana_gid
                                         }
                                         ]}}
                        task_instance.create_task(body,{})
        except Exception as exc:
            raise ValidationError(
                _('Please check the workspace ID or the app token')) from exc
