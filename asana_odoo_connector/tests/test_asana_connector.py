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
from unittest.mock import MagicMock, patch
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAsanaConnector(TransactionCase):
    """Test suite for the Asana Odoo Connector module."""

    def setUp(self):
        super().setUp()
        self.params = self.env['ir.config_parameter'].sudo()
        self.params.set_str(
            'asana_odoo_connector.workspace_gid', '123456789'
        )
        self.params.set_str(
            'asana_odoo_connector.app_token', 'test_app_token_secret'
        )
        self.settings = self.env['res.config.settings'].create({
            'workspace_gid': '123456789',
            'app_token': 'test_app_token_secret',
        })

    def test_action_test_asana_success(self):
        """Test successful connection verification to Asana."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch('requests.get', return_value=mock_response):
            action = self.settings.action_test_asana()
            self.assertEqual(action.get('type'), 'ir.actions.client')
            self.assertEqual(
                action.get('params', {}).get('type'), 'success'
            )
            is_successful = self.params.get_bool(
                'asana_odoo_connector.connection_successful'
            )
            self.assertTrue(is_successful)

    def test_action_test_asana_failure(self):
        """Test connection failure when Asana API returns an error status."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        with patch('requests.get', return_value=mock_response):
            action = self.settings.action_test_asana()
            self.assertEqual(action.get('type'), 'ir.actions.client')
            self.assertEqual(
                action.get('params', {}).get('type'), 'danger'
            )

    def test_action_test_asana_missing_credentials(self):
        """Test connection test when credentials are not configured."""
        self.params.set_str('asana_odoo_connector.workspace_gid', '')
        self.params.set_str('asana_odoo_connector.app_token', '')
        empty_settings = self.env['res.config.settings'].create({
            'workspace_gid': False,
            'app_token': False,
        })
        action = empty_settings.action_test_asana()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('params', {}).get('type'), 'danger')

    @patch('asana.ProjectsApi')
    @patch('asana.SectionsApi')
    @patch('asana.TasksApi')
    def test_action_import_projects_and_tasks(
        self, mock_tasks_api, mock_sections_api, mock_projects_api
    ):
        """Test importing projects, stages, and tasks from Asana."""
        projects_instance = mock_projects_api.return_value
        sections_instance = mock_sections_api.return_value
        tasks_instance = mock_tasks_api.return_value

        projects_instance.get_projects.return_value = [
            {'gid': 'asana_proj_101', 'name': 'Asana Alpha Project'}
        ]
        sections_instance.get_sections_for_project.return_value = [
            {'gid': 'asana_sec_201', 'name': 'Backlog'},
            {'gid': 'asana_sec_202', 'name': 'In Progress'},
        ]

        def mock_get_tasks(section_gid, opts):
            if section_gid == 'asana_sec_201':
                return [{'gid': 'asana_tsk_301', 'name': 'Task Alpha'}]
            return []

        tasks_instance.get_tasks_for_section.side_effect = mock_get_tasks

        self.settings.action_import_projects()

        project = self.env['project.project'].search(
            [('asana_gid', '=', 'asana_proj_101')], limit=1
        )
        self.assertTrue(project, "Project should have been created.")
        self.assertEqual(project.name, 'Asana Alpha Project')
        self.assertEqual(len(project.type_ids), 2)

        task = self.env['project.task'].search(
            [('asana_gid', '=', 'asana_tsk_301'),
             ('project_id', '=', project.id)], limit=1
        )
        self.assertTrue(task, "Task should have been created.")
        self.assertEqual(task.name, 'Task Alpha')
        self.assertEqual(task.stage_id.asana_gid, 'asana_sec_201')

        # Re-import to verify deduplication
        self.settings.action_import_projects()
        all_projects = self.env['project.project'].search(
            [('asana_gid', '=', 'asana_proj_101')]
        )
        self.assertEqual(
            len(all_projects), 1, "Duplicate project should not be created."
        )
        all_tasks = self.env['project.task'].search(
            [('asana_gid', '=', 'asana_tsk_301'),
             ('project_id', '=', project.id)]
        )
        self.assertEqual(
            len(all_tasks), 1, "Duplicate task should not be created."
        )

    def test_action_import_missing_credentials(self):
        """Test UserError is raised on import without credentials."""
        self.params.set_str('asana_odoo_connector.workspace_gid', '')
        self.params.set_str('asana_odoo_connector.app_token', '')
        empty_settings = self.env['res.config.settings'].create({
            'workspace_gid': False,
            'app_token': False,
        })
        with self.assertRaises(UserError):
            empty_settings.action_import_projects()

    @patch('asana.ProjectsApi')
    @patch('asana.SectionsApi')
    @patch('asana.TasksApi')
    def test_action_export_to_asana(
        self, mock_tasks_api, mock_sections_api, mock_projects_api
    ):
        """Test exporting projects, stages, and tasks from Odoo to Asana."""
        projects_instance = mock_projects_api.return_value
        sections_instance = mock_sections_api.return_value
        tasks_instance = mock_tasks_api.return_value

        projects_instance.create_project_for_workspace.return_value = {
            'gid': 'asana_exp_proj_900'
        }
        sections_instance.create_section_for_project.return_value = {
            'gid': 'asana_exp_sec_901'
        }
        tasks_instance.create_task.return_value = {
            'gid': 'asana_exp_tsk_902'
        }

        project = self.env['project.project'].create({
            'name': 'Odoo Local Project',
            'type_ids': [
                Command.create({'name': 'Design'}),
            ],
        })
        task = self.env['project.task'].create({
            'name': 'Design UI',
            'project_id': project.id,
            'stage_id': project.type_ids[0].id,
        })

        project.action_export_to_asana()

        self.assertEqual(project.asana_gid, 'asana_exp_proj_900')
        self.assertEqual(project.type_ids[0].asana_gid, 'asana_exp_sec_901')
        self.assertEqual(task.asana_gid, 'asana_exp_tsk_902')

    def test_action_export_missing_credentials(self):
        """Test UserError is raised on export without credentials."""
        self.params.set_str('asana_odoo_connector.workspace_gid', '')
        self.params.set_str('asana_odoo_connector.app_token', '')
        project = self.env['project.project'].create({
            'name': 'No Credentials Project'
        })
        with self.assertRaises(UserError):
            project.action_export_to_asana()
