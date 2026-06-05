# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProjectProject(TransactionCase):
    """Test exporting Odoo projects to Asana."""

    def test_action_export_to_asana_creates_project_sections_and_tasks(self):
        """A project without Asana GID is exported with sections and tasks."""
        self.env['ir.config_parameter'].sudo().set_param(
            'asana_odoo_connector.app_token', 'token_4')
        self.env['ir.config_parameter'].sudo().set_param(
            'asana_odoo_connector.workspace_gid', 'workspace_gid_4')
        project = self.env['project.project'].create({
            'name': 'Odoo Project',
        })
        stage = self.env['project.task.type'].create({
            'name': 'Odoo Section',
            'project_ids': [(4, project.id)],
        })
        task = self.env['project.task'].create({
            'name': 'Odoo Task',
            'project_id': project.id,
            'stage_id': stage.id,
        })
        configuration = MagicMock()
        api_client = MagicMock()
        project_api = MagicMock()
        section_api = MagicMock()
        task_api = MagicMock()
        project_api.create_project_for_workspace.return_value = {
            'gid': 'exported_project_gid',
        }
        section_api.create_section_for_project.return_value = {
            'gid': 'exported_section_gid',
        }
        asana_mock = SimpleNamespace(
            Configuration=MagicMock(return_value=configuration),
            ApiClient=MagicMock(return_value=api_client),
            ProjectsApi=MagicMock(return_value=project_api),
            SectionsApi=MagicMock(return_value=section_api),
            TasksApi=MagicMock(return_value=task_api),
        )

        with patch(
                'odoo.addons.asana_odoo_connector.models.'
                'project_project.asana',
                asana_mock,
                create=True):
            project.action_export_to_asana()

        self.assertEqual(project.asana_gid, 'exported_project_gid')
        self.assertEqual(stage.asana_gid, 'exported_section_gid')
        project_api.create_project_for_workspace.assert_called_once_with(
            {'data': {'name': 'Odoo Project'}},
            'workspace_gid_4',
            {},
        )
        section_api.create_section_for_project.assert_called_once_with(
            'exported_project_gid',
            {'body': {'data': {'name': 'Odoo Section'}}},
        )
        task_api.create_task.assert_called_once_with(
            {'data': {
                'name': task.name,
                'workspace': 'workspace_gid_4',
                'projects': 'exported_project_gid',
                'memberships': [{
                    'project': 'exported_project_gid',
                    'section': 'exported_section_gid',
                }],
            }},
            {},
        )
