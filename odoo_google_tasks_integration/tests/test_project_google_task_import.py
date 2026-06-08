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
class TestProjectGoogleTaskImport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({'name': 'Wizard Project'})
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
        cls.wizard = cls.env['project.google.task.import'].create({})

    @patch('odoo.addons.odoo_google_tasks_integration.wizard.project_google_task_import.requests.get')
    def test_action_import_tasks_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {'id': 'task-1', 'title': 'Imported Task 1', 'due': '2026-05-18T00:00:00.000Z'},
                {'id': 'task-2', 'title': 'Imported Task 2'},
            ],
        }
        mock_get.return_value = mock_response

        action = self.wizard.action_import_tasks()

        imported_tasks = self.env['project.task'].search([('google_task', 'in', ['task-1', 'task-2'])])
        self.assertEqual(len(imported_tasks), 2)
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'success')

    @patch('odoo.addons.odoo_google_tasks_integration.wizard.project_google_task_import.requests.get')
    def test_action_import_tasks_skips_existing_tasks(self, mock_get):
        self.env['project.task'].create({
            'name': 'Existing Imported Task',
            'project_id': self.project.id,
            'google_task': 'existing-task',
        })
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {'id': 'existing-task', 'title': 'Existing Imported Task'},
            ],
        }
        mock_get.return_value = mock_response

        action = self.wizard.action_import_tasks()

        self.assertIn('Imported 0 tasks', action['params']['message'])

    @patch('odoo.addons.odoo_google_tasks_integration.wizard.project_google_task_import.requests.get')
    def test_action_import_tasks_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'api failure'
        mock_get.return_value = mock_response

        action = self.wizard.action_import_tasks()

        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'warning')

    @patch('odoo.addons.odoo_google_tasks_integration.models.project_task.ProjectTask.action_sync_task_to_google')
    def test_action_export_task(self, mock_sync):
        task_1 = self.env['project.task'].create({
            'name': 'Export Task 1',
            'project_id': self.project.id,
        })
        task_2 = self.env['project.task'].create({
            'name': 'Export Task 2',
            'project_id': self.project.id,
        })
        wizard = self.env['project.google.task.import'].create({
            'task_ids': [Command.set([task_1.id, task_2.id])],
        })

        action = wizard.action_export_task()

        self.assertEqual(mock_sync.call_count, 2)
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'success')
