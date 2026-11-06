#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged

from .common import REQUEST, GoogleTasksCommon, mock_response


@tagged('post_install', '-at_install')
class TestProjectUser(GoogleTasksCommon):
    """A project user, who cannot read the credentials, still exports and
    imports the tasks."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env, login='gtask_project_user',
            groups='base.group_user,project.group_project_user')
        cls.project.privacy_visibility = 'employees'

    def test_credentials_hidden(self):
        """The credentials and tokens stay with the project
        administrators."""
        with self.assertRaises(AccessError):
            self.credential.with_user(self.user).read(
                ['hangout_client_secret'])

    @patch(REQUEST)
    def test_export_and_import(self, mock_request):
        """The project user exports a task and imports the Google tasks."""
        env = self.env(user=self.user)
        task = env['project.task'].create(
            {'name': 'User Task', 'project_id': self.project.id})
        mock_request.return_value = mock_response(json={'id': 'g-user'})
        action = task.action_sync_task_to_google()
        self.assertEqual(action['params']['type'], 'success')
        self.assertEqual(task.google_task, 'g-user')
        mock_request.return_value = mock_response(json={'items': [
            {'id': 'g-user', 'title': 'User Task'},
            {'id': 'g-new', 'title': 'From Google'},
        ]})
        wizard = env['project.google.task.import'].create(
            {'project_id': self.project.id})
        wizard.action_import_tasks()
        imported = env['project.task'].search([('google_task', '=', 'g-new')])
        self.assertEqual(imported.name, 'From Google')
        self.assertEqual(imported.project_id, self.project)
