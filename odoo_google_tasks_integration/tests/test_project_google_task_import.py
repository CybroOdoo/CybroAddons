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

from odoo.tests import tagged

from .common import REQUEST, GoogleTasksCommon, mock_response


@tagged('post_install', '-at_install')
class TestProjectGoogleTaskImport(GoogleTasksCommon):

    @patch(REQUEST)
    def test_import_tasks(self, mock_request):
        existing = self.env['project.task'].create({
            'name': 'Already imported', 'google_task': 'g-existing'})
        mock_request.side_effect = [
            mock_response(json={'items': [
                {'id': 'g-existing', 'title': 'Already imported'},
                {'id': 'g-parent', 'title': 'Parent', 'notes': 'Some notes',
                 'due': '2026-06-01T00:00:00.000Z'},
            ], 'nextPageToken': 'page-2'}),
            mock_response(json={'items': [
                {'id': 'g-child', 'title': 'Child', 'parent': 'g-parent'},
            ]}),
        ]
        wizard = self.env['project.google.task.import'].create(
            {'project_id': self.project.id})
        action = wizard.action_import_tasks()
        self.assertIn('2', action['params']['message'])
        self.assertEqual(mock_request.call_args.kwargs['params']['pageToken'],
                         'page-2')
        tasks = self.env['project.task'].search(
            [('google_task', 'in', ['g-existing', 'g-parent', 'g-child'])])
        self.assertEqual(len(tasks), 3)
        parent = tasks.filtered(lambda t: t.google_task == 'g-parent')
        child = tasks.filtered(lambda t: t.google_task == 'g-child')
        self.assertTrue(parent.is_imported)
        self.assertFalse(existing.is_imported)
        self.assertIn('Some notes', parent.description)
        self.assertEqual(str(parent.date_deadline.date()), '2026-06-01')
        self.assertEqual(parent.project_id, self.project)
        self.assertEqual(child.parent_id, parent)

    @patch(REQUEST)
    def test_import_private_tasks(self, mock_request):
        mock_request.return_value = mock_response(json={'items': [
            {'id': 'g-parent', 'title': 'Parent'},
            {'id': 'g-child', 'title': 'Child', 'parent': 'g-parent'},
        ]})
        self.env['project.google.task.import'].create({}).action_import_tasks()
        tasks = self.env['project.task'].search(
            [('google_task', 'in', ['g-parent', 'g-child'])])
        self.assertEqual(len(tasks), 2)
        self.assertFalse(tasks.project_id)
        self.assertFalse(tasks.parent_id)
        self.assertEqual(tasks.user_ids, self.env.user)

    @patch(REQUEST)
    def test_import_error(self, mock_request):
        mock_request.return_value = mock_response(401, text='unauthorized')
        wizard = self.env['project.google.task.import'].create({})
        with self.assertRaisesRegex(Exception, 'unauthorized'):
            wizard.action_import_tasks()

    @patch(REQUEST)
    def test_export_tasks(self, mock_request):
        task = self.env['project.task'].create(
            {'name': 'Export me', 'project_id': self.project.id})
        mock_request.return_value = mock_response(json={'id': 'exported'})
        wizard = self.env['project.google.task.import'].create({
            'export_import_selection': 'export',
            'task_ids': [task.id]})
        action = wizard.action_export_task()
        self.assertEqual(action['params']['next']['type'],
                         'ir.actions.act_window_close')
        self.assertEqual(task.google_task, 'exported')
