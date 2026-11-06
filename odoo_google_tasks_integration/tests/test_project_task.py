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
import json
from unittest.mock import patch

from odoo.fields import Command
from odoo.tests import tagged

from .common import MODULE, REQUEST, GoogleTasksCommon, mock_response


@tagged('post_install', '-at_install')
class TestProjectTask(GoogleTasksCommon):

    def _task(self, **vals):
        return self.env['project.task'].create(
            dict({'name': 'Main Task', 'project_id': self.project.id}, **vals))

    @patch(REQUEST)
    def test_export_task_with_subtasks(self, mock_request):
        task = self._task(
            description='<p>Task description</p>',
            date_deadline='2026-05-20 10:00:00',
            child_ids=[Command.create({'name': 'Child 1',
                                       'project_id': self.project.id}),
                       Command.create({'name': 'Child 2',
                                       'project_id': self.project.id})])
        mock_request.side_effect = [
            mock_response(json={'id': 'main'}),
            mock_response(json={'id': 'sub-1'}),
            mock_response(json={'id': 'sub-2'}),
        ]
        action = task.action_sync_task_to_google()
        # The action goes back to the web client as JSON
        json.dumps(action)
        self.assertEqual(action['params']['type'], 'success')
        self.assertTrue(task.is_add_in_gtask)
        self.assertEqual(task.google_task, 'main')
        self.assertEqual(sorted(task.child_ids.mapped('google_task')),
                         ['sub-1', 'sub-2'])
        main_call, sub_call, _sub_call = mock_request.call_args_list
        self.assertEqual(main_call.args[0], 'POST')
        self.assertEqual(main_call.kwargs['json'], {
            'title': 'Main Task', 'notes': 'Task description',
            'due': '2026-05-20T00:00:00Z'})
        self.assertEqual(sub_call.kwargs['params'], {'parent': 'main'})

    @patch(REQUEST)
    def test_export_updates_existing_task(self, mock_request):
        task = self._task(google_task='existing')
        mock_request.return_value = mock_response(json={'id': 'existing'})
        task.action_sync_task_to_google()
        mock_request.assert_called_once()
        self.assertEqual(mock_request.call_args.args[0], 'PATCH')
        self.assertTrue(mock_request.call_args.args[1].endswith('/existing'))

    @patch(REQUEST)
    def test_export_recreates_task_deleted_in_google(self, mock_request):
        task = self._task(google_task='deleted')
        mock_request.side_effect = [mock_response(404),
                                    mock_response(json={'id': 'new'})]
        task.action_sync_task_to_google()
        self.assertEqual(mock_request.call_args.args[0], 'POST')
        self.assertEqual(task.google_task, 'new')

    @patch(REQUEST)
    def test_export_several_tasks(self, mock_request):
        tasks = self._task(name='A') | self._task(name='B')
        mock_request.side_effect = [mock_response(json={'id': 'a'}),
                                    mock_response(json={'id': 'b'})]
        tasks.action_sync_task_to_google()
        self.assertEqual(tasks.mapped('google_task'), ['a', 'b'])

    @patch(REQUEST)
    def test_export_failure_keeps_other_tasks(self, mock_request):
        tasks = self._task(name='A') | self._task(name='B')
        mock_request.side_effect = [mock_response(json={'id': 'a'}),
                                    mock_response(400, text='bad request')]
        action = tasks.action_sync_task_to_google()
        self.assertEqual(action['params']['type'], 'warning')
        self.assertIn('bad request', action['params']['message'])
        self.assertEqual(tasks.mapped('google_task'), ['a', False])

    @patch(REQUEST)
    def test_create_with_flag_exports(self, mock_request):
        mock_request.return_value = mock_response(json={'id': 'created'})
        task = self._task(is_add_in_gtask=True)
        self.assertEqual(task.google_task, 'created')

    @patch(REQUEST)
    def test_changes_update_exported_task(self, mock_request):
        task = self._task(google_task='existing', is_add_in_gtask=False)
        mock_request.return_value = mock_response(json={'id': 'existing'})
        task.priority = '1'
        mock_request.assert_not_called()
        task.name = 'Renamed'
        self.assertEqual(mock_request.call_args.args[0], 'PATCH')
        self.assertEqual(mock_request.call_args.kwargs['json']['title'],
                         'Renamed')

    @patch(REQUEST)
    def test_not_exported_task_is_not_synced(self, mock_request):
        task = self._task()
        task.name = 'Renamed'
        mock_request.assert_not_called()

    @patch(REQUEST)
    def test_save_does_not_fail_when_google_fails(self, mock_request):
        task = self._task(google_task='existing')
        mock_request.return_value = mock_response(500, text='server error')
        with self.assertLogs(f'{MODULE}.models.project_task', 'WARNING'):
            task.name = 'Renamed'
        self.assertEqual(task.name, 'Renamed')
        self.assertIn('server error', task.message_ids[0].body)

    def test_copy_does_not_keep_google_task(self):
        task = self._task(google_task='existing', is_imported=True)
        copy = task.with_context(skip_gtask_sync=True).copy()
        self.assertFalse(copy.google_task)
        self.assertFalse(copy.is_imported)
