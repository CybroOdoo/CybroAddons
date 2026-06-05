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
class TestResConfigSettings(TransactionCase):
    """Test Asana connector settings actions."""

    def test_action_test_asana_success(self):
        """A successful Asana workspace response returns success notification."""
        settings = self.env['res.config.settings'].create({
            'workspace_gid': 'workspace_gid_1',
            'app_token': 'token_1',
        })

        with patch(
                'odoo.addons.asana_odoo_connector.models.'
                'res_config_settings.requests.get') as mock_get:
            mock_get.return_value = SimpleNamespace(status_code=200)

            action = settings.action_test_asana()

        mock_get.assert_called_once_with(
            'https://app.asana.com/api/1.0/workspaces/workspace_gid_1',
            headers={'Authorization': 'Bearer token_1'},
            timeout=10,
        )
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'success')
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param(
                'asana_odoo_connector.connection_successful'),
            'True',
            "Successful connection should be stored in system parameters."
        )

    def test_action_test_asana_failure(self):
        """An unsuccessful Asana response returns danger notification."""
        settings = self.env['res.config.settings'].create({
            'workspace_gid': 'workspace_gid_2',
            'app_token': 'token_2',
        })

        with patch(
                'odoo.addons.asana_odoo_connector.models.'
                'res_config_settings.requests.get') as mock_get:
            mock_get.return_value = SimpleNamespace(status_code=401)

            action = settings.action_test_asana()

        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'danger')

    def test_action_import_projects_creates_project_stages_and_tasks(self):
        """Projects, sections, and tasks returned by Asana are imported."""
        settings = self.env['res.config.settings'].create({
            'workspace_gid': 'workspace_gid_3',
            'app_token': 'token_3',
        })
        configuration = MagicMock()
        api_client = MagicMock()
        project_api = MagicMock()
        section_api = MagicMock()
        task_api = MagicMock()

        project_api.get_projects.return_value = [{
            'gid': 'asana_project_gid',
            'name': 'Asana Project',
        }]
        section_api.get_sections_for_project.return_value = [{
            'gid': 'asana_section_gid',
            'name': 'Asana Section',
        }]
        task_api.get_tasks_for_section.return_value = [{
            'gid': 'asana_task_gid',
            'name': 'Asana Task',
        }]
        asana_mock = SimpleNamespace(
            Configuration=MagicMock(return_value=configuration),
            ApiClient=MagicMock(return_value=api_client),
            ProjectsApi=MagicMock(return_value=project_api),
            SectionsApi=MagicMock(return_value=section_api),
            TasksApi=MagicMock(return_value=task_api),
        )

        with patch(
                'odoo.addons.asana_odoo_connector.models.'
                'res_config_settings.asana',
                asana_mock,
                create=True):
            settings.action_import_projects()

        project = self.env['project.project'].search([
            ('asana_gid', '=', 'asana_project_gid')
        ])
        stage = self.env['project.task.type'].search([
            ('asana_gid', '=', 'asana_section_gid'),
            ('project_ids', '=', project.id),
        ])
        task = self.env['project.task'].search([
            ('asana_gid', '=', 'asana_task_gid'),
            ('project_id', '=', project.id),
        ])

        self.assertEqual(project.name, 'Asana Project')
        self.assertEqual(stage.name, 'Asana Section')
        self.assertEqual(task.name, 'Asana Task')
        self.assertEqual(task.stage_id, stage)
