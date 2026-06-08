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

import datetime
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProjectTask(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({'name': 'Google Task Project'})
        cls.credential = cls.env.ref(
            'odoo_google_tasks_integration.project_google_credential_data'
        )
        cls.credential.write({
            'hangout_client': 'client-id',
            'hangout_client_secret': 'client-secret',
            'hangout_company_refresh_token': 'refresh-token',
            'hangout_company_access_token': 'access-token',
            'hangout_company_access_token_expiry': fields.Datetime.now() + datetime.timedelta(hours=1),
        })

    @patch('odoo.addons.odoo_google_tasks_integration.models.project_task.ProjectTask.action_sync_task_to_google')
    def test_create_syncs_task_when_flag_enabled(self, mock_sync):
        task = self.env['project.task'].create({
            'name': 'Sync On Create',
            'project_id': self.project.id,
            'is_add_in_gtask': True,
        })

        self.assertTrue(task.is_add_in_gtask)
        self.assertTrue(mock_sync.called)

    @patch('odoo.addons.odoo_google_tasks_integration.models.project_task.ProjectTask.action_sync_task_to_google')
    def test_write_syncs_task_when_flag_set(self, mock_sync):
        task = self.env['project.task'].create({
            'name': 'Sync On Write',
            'project_id': self.project.id,
        })

        task.write({'is_add_in_gtask': True})

        self.assertTrue(mock_sync.called)

    @patch('odoo.addons.odoo_google_tasks_integration.models.project_task.requests.post')
    @patch('odoo.addons.odoo_google_tasks_integration.models.project_task.requests.patch')
    def test_action_sync_task_to_google_creates_main_task_and_subtask(self, mock_patch, mock_post):
        task = self.env['project.task'].create({
            'name': 'Main Task',
            'project_id': self.project.id,
            'description': '<p>Task description</p>',
            'date_deadline': '2026-05-20',
            'child_ids': [
                Command.create({
                    'name': 'Child Task',
                    'project_id': self.project.id,
                }),
            ],
        })

        main_response = MagicMock()
        main_response.status_code = 200
        main_response.json.return_value = {'id': 'main-google-id'}
        subtask_response = MagicMock()
        subtask_response.status_code = 200
        subtask_response.json.return_value = {'id': 'sub-google-id'}
        move_response = MagicMock()
        move_response.status_code = 200
        mock_post.side_effect = [main_response, subtask_response, move_response]

        result = task.action_sync_task_to_google()

        self.assertEqual(task.google_task, 'main-google-id')
        self.assertEqual(task.child_ids.google_task, 'sub-google-id')
        self.assertEqual(result, move_response)
        self.assertFalse(mock_patch.called)

    @patch('odoo.addons.odoo_google_tasks_integration.models.project_task.requests.post')
    @patch('odoo.addons.odoo_google_tasks_integration.models.project_task.requests.patch')
    def test_action_sync_task_to_google_updates_existing_google_task(self, mock_patch, mock_post):
        task = self.env['project.task'].create({
            'name': 'Existing Task',
            'project_id': self.project.id,
            'description': 'Existing description',
            'google_task': 'existing-google-id',
        })
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {'id': 'existing-google-id'}
        mock_patch.return_value = response

        result = task.action_sync_task_to_google()

        self.assertFalse(result)
        self.assertTrue(mock_patch.called)
        self.assertFalse(mock_post.called)

    @patch('odoo.addons.odoo_google_tasks_integration.models.project_task.requests.post')
    def test_action_sync_task_to_google_returns_warning_on_failure(self, mock_post):
        task = self.env['project.task'].create({
            'name': 'Failed Task',
            'project_id': self.project.id,
        })
        response = MagicMock()
        response.status_code = 400
        response.text = 'failure'
        mock_post.return_value = response

        action = task.action_sync_task_to_google()

        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'warning')
