# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Cybrosys Technologies(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch

from odoo.exceptions import MissingError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

@tagged('post_install', '-at_install')
class TestResUsersTodoist(TransactionCase):
    """Test Todoist res_users integration and synchronization."""

    def test_fetch_token_returns_todoist_token(self):
        """Configured Todoist token is returned from the user."""
        self.env.user.todoist_token = 'todoist_token'

        self.assertEqual(self.env.user._fetch_token(), 'todoist_token')

    def test_action_sync_todoist_with_odoo_creates_projects_tasks_and_tags(self):
        """Todoist projects, tasks, and labels are created in Odoo."""
        self.env.user.todoist_token = 'todoist_token'

        def _mock_get_todoist_data(token, project=False):
            self.assertEqual(token, 'todoist_token')
            if project:
                return [{
                    'id': 'todoist_project_2',
                    'name': 'Synced Todoist Project',
                }]
            return [{
                'id': 'todoist_task_2',
                'project_id': 'todoist_project_2',
                'content': 'Synced Todoist Task',
                'description': 'Created from Todoist',
                'due': {'date': '2026-05-21'},
                'labels': ['Important', 'Client'],
            }]

        with patch(
                'odoo.addons.todoist_project.models.res_users.'
                '_get_todoist_projects_tasks',
                side_effect=_mock_get_todoist_data):
            action = self.env.user.action_sync_todoist_with_odoo()

        project = self.env['project.project'].search([
            ('todo_project', '=', 'todoist_project_2'),
        ], limit=1)
        task = self.env['project.task'].search([
            ('todo_task', '=', 'todoist_task_2'),
        ], limit=1)

        self.assertTrue(project)
        self.assertEqual(project.name, 'Synced Todoist Project')
        self.assertTrue(task)
        self.assertEqual(task.project_id, project)
        self.assertEqual(task.name, 'Synced Todoist Task')
        self.assertIn('Created from Todoist', task.description)
        self.assertEqual(str(task.date_deadline.date()), '2026-05-21')
        self.assertEqual(set(task.tag_ids.mapped('name')),
                         {'Important', 'Client'})
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'success')

    def test_fetch_token_requires_todoist_token(self):
        """Todoist sync requires a configured user token."""
        self.env.user.todoist_token = False

        with self.assertRaises(MissingError):
            self.env.user._fetch_token()
