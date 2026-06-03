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


class ProjectTaskTestCase(TransactionCase):

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
        write_values = {}
        for field_name in ('google_task', 'is_add_in_gtask'):
            if field_name in defaults:
                write_values[field_name] = defaults.pop(field_name)
        task = self.env['project.task'].with_context(skip_gtask_sync=True).create(
            defaults
        )
        if write_values:
            task.with_context(skip_gtask_sync=True).write(write_values)
        return task.with_context({})


@tagged('-at_install', 'post_install')
class TestProjectTask(ProjectTaskTestCase):

    def test_create_syncs_task_when_google_flag_is_enabled(self):
        with patch(
            'odoo.addons.odoo_google_tasks_integration.models.project_task'
            '.ProjectTask.action_sync_task_to_google',
        ) as sync:
            task = self.env['project.task'].create({
                'name': 'Created Task',
                'project_id': self.google_project.id,
                'is_add_in_gtask': True,
            })

        self.assertTrue(task)
        sync.assert_called_once()

    def test_write_syncs_task_when_sync_field_changes(self):
        task = self._create_task(is_add_in_gtask=True)

        with patch(
            'odoo.addons.odoo_google_tasks_integration.models.project_task'
            '.ProjectTask.action_sync_task_to_google',
        ) as sync:
            task.write({'name': 'Updated Task'})

        sync.assert_called_once()

    def test_write_skips_sync_when_context_requests_it(self):
        task = self._create_task(is_add_in_gtask=True)

        with patch(
            'odoo.addons.odoo_google_tasks_integration.models.project_task'
            '.ProjectTask.action_sync_task_to_google',
        ) as sync:
            task.with_context(skip_gtask_sync=True).write({'name': 'Updated Task'})

        sync.assert_not_called()

    def test_action_sync_task_to_google_creates_google_task(self):
        task = self._create_task(
            name='Main Task',
            description='<p>Plain <b>note</b></p>',
            date_deadline='2026-05-27',
        )
        response = self._make_response(
            status_code=200,
            payload={'id': 'google-main-task'},
        )

        with patch(
            'odoo.addons.odoo_google_tasks_integration.models.project_task.requests.post',
            return_value=response,
        ) as post:
            result = task.action_sync_task_to_google()

        self.assertEqual(result, response)
        self.assertTrue(task.is_add_in_gtask)
        self.assertEqual(task.google_task, 'google-main-task')
        self.assertEqual(post.call_args.kwargs['json']['title'], 'Main Task')
        self.assertEqual(post.call_args.kwargs['json']['notes'], 'Plain note')
        self.assertEqual(
            post.call_args.kwargs['json']['due'],
            '2026-05-27T00:00:00Z',
        )

    def test_action_sync_task_to_google_updates_existing_task(self):
        task = self._create_task(
            name='Existing Task',
            google_task='existing-google-id',
            is_add_in_gtask=True,
        )
        response = self._make_response(
            status_code=200,
            payload={'id': 'existing-google-id'},
        )

        with patch(
            'odoo.addons.odoo_google_tasks_integration.models.project_task.requests.patch',
            return_value=response,
        ) as patch_request:
            result = task.action_sync_task_to_google()

        self.assertEqual(result, response)
        patch_request.assert_called_once()
        self.assertIn('existing-google-id', patch_request.call_args.args[0])

    def test_action_sync_task_to_google_refreshes_token_after_unauthorized(self):
        task = self._create_task(name='Unauthorized Task')
        unauthorized = self._make_response(status_code=401)
        success = self._make_response(status_code=200, payload={'id': 'after-refresh'})

        with patch.object(
            type(self.credential),
            'action_google_task_company_refresh_token',
        ) as refresh_token, patch(
            'odoo.addons.odoo_google_tasks_integration.models.project_task.requests.post',
            side_effect=[unauthorized, success],
        ) as post:
            result = task.action_sync_task_to_google()

        self.assertEqual(result, success)
        refresh_token.assert_called_once()
        self.assertEqual(post.call_count, 2)
        self.assertEqual(task.google_task, 'after-refresh')

    def test_action_sync_task_to_google_syncs_child_tasks(self):
        parent = self._create_task(name='Parent Task')
        child = self._create_task(name='Child Task', parent_id=parent.id)
        main_response = self._make_response(status_code=200, payload={'id': 'main-id'})
        child_response = self._make_response(status_code=200, payload={'id': 'child-id'})
        move_response = self._make_response(status_code=200, payload={})

        with patch(
            'odoo.addons.odoo_google_tasks_integration.models.project_task.requests.post',
            side_effect=[main_response, child_response, move_response],
        ) as post:
            parent.action_sync_task_to_google()

        self.assertEqual(child.google_task, 'child-id')
        self.assertEqual(post.call_count, 3)
        self.assertIn('/move', post.call_args_list[2].args[0])
        self.assertEqual(post.call_args_list[2].kwargs['json']['parent'], 'main-id')
