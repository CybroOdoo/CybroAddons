# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<http://www.cybrosys.com>)
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
#############################################################################from unittest.mock import MagicMock, patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class ProjectGoogleTaskImportTestCase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.credential = cls.env.ref(
            'odoo_google_tasks_integration.project_google_credential_data'
        )
        cls.google_project = cls.env.ref(
            'odoo_google_tasks_integration.google_project'
        )
        cls.credential.write({
            'hangout_client': 'client-id',
            'hangout_client_secret': 'client-secret',
            'hangout_redirect_uri': 'http://localhost:8069/google_task_authentication',
            'hangout_company_access_token': 'access-token',
            'hangout_company_refresh_token': 'refresh-token',
        })

    def _make_response(self, status_code=200, payload=None, text=''):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = payload or {}
        response.text = text
        return response

    def _create_task(self, **values):
        defaults = {
            'name': 'Test Google Task',
            'project_id': self.google_project.id,
        }
        defaults.update(values)
        return self.env['project.task'].with_context(skip_gtask_sync=True).create(
            defaults
        ).with_context({})


@tagged('-at_install', 'post_install')
class TestProjectGoogleTaskImportWizard(ProjectGoogleTaskImportTestCase):

    def test_action_import_tasks_creates_tasks_and_parent_links(self):
        wizard = self.env['project.google.task.import'].create({})
        response = self._make_response(
            status_code=200,
            payload={
                'items': [
                    {
                        'id': 'google-parent',
                        'title': 'Google Parent',
                        'due': '2026-05-27T00:00:00.000Z',
                    },
                    {
                        'id': 'google-child',
                        'title': 'Google Child',
                        'parent': 'google-parent',
                    },
                ],
            },
        )

        with patch(
            'odoo.addons.odoo_google_tasks_integration.wizard'
            '.project_google_task_import.requests.get',
            return_value=response,
        ):
            action = wizard.action_import_tasks()

        parent = self.env['project.task'].search(
            [('google_task', '=', 'google-parent')],
            limit=1,
        )
        child = self.env['project.task'].search(
            [('google_task', '=', 'google-child')],
            limit=1,
        )
        self.assertTrue(parent)
        self.assertTrue(child)
        self.assertEqual(child.parent_id, parent)
        self.assertTrue(parent.is_imported)
        self.assertEqual(parent.project_id, self.google_project)
        self.assertEqual(action['params']['type'], 'success')

    def test_action_import_tasks_refreshes_token_on_unauthorized(self):
        wizard = self.env['project.google.task.import'].create({})
        unauthorized = self._make_response(status_code=401)
        success = self._make_response(status_code=200, payload={'items': []})

        with patch.object(
            type(self.credential),
            'action_google_task_company_refresh_token',
        ) as refresh_token, patch(
            'odoo.addons.odoo_google_tasks_integration.wizard'
            '.project_google_task_import.requests.get',
            side_effect=[unauthorized, success],
        ) as get:
            action = wizard.action_import_tasks()

        refresh_token.assert_called_once()
        self.assertEqual(get.call_count, 2)
        self.assertEqual(action['params']['type'], 'success')

    def test_action_import_tasks_returns_error_notification(self):
        wizard = self.env['project.google.task.import'].create({})
        response = self._make_response(status_code=500, text='server error')

        with patch(
            'odoo.addons.odoo_google_tasks_integration.wizard'
            '.project_google_task_import.requests.get',
            return_value=response,
        ):
            action = wizard.action_import_tasks()

        self.assertEqual(action['params']['type'], 'danger')
        self.assertIn('server error', action['params']['message'])

    def test_action_export_task_syncs_selected_tasks(self):
        task = self._create_task(name='Export Me')
        wizard = self.env['project.google.task.import'].create({
            'task_ids': [(6, 0, task.ids)],
        })

        with patch(
            'odoo.addons.odoo_google_tasks_integration.models.project_task'
            '.ProjectTask.action_sync_task_to_google',
        ) as sync:
            action = wizard.action_export_task()

        sync.assert_called_once()
        self.assertEqual(action['params']['type'], 'success')
