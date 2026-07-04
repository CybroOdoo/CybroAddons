# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################
from types import SimpleNamespace
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProjectTaskGoogleCalendar(TransactionCase):
    """Test project task synchronization with Google Calendar."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.write({
            'user_token': 'google_user_token',
            'api_key': 'google_api_key',
            'google_user_mail': 'calendar.user@example.com',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Calendar Customer',
            'email': 'customer@example.com',
        })
        cls.assigned_user = cls.env['res.users'].create({
            'name': 'Calendar Assignee',
            'login': 'calendar_assignee',
            'email': 'assignee@example.com',
        })
        cls.project = cls.env['project.project'].create({
            'name': 'calendar project',
        })

    @patch(
        'odoo.addons.sync_task_with_google_calender.models.'
        'project_task.requests.post'
    )
    def test_create_task_syncs_google_calendar_event(self, mock_post):
        """Creating a marked task creates and stores a Google Calendar event."""
        mock_post.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: {
                'id': 'google_event_1',
                'creator': {'email': 'calendar.user@example.com'},
            },
        )

        task = self.env['project.task'].create({
            'name': 'Calendar Task',
            'description': 'Discuss project status',
            'project_id': self.project.id,
            'partner_id': self.partner.id,
            'user_ids': [(6, 0, [self.assigned_user.id])],
            'date_deadline': '2026-05-21',
            'is_add_in_gcalendar': True,
        })

        expected_url = (
            'https://www.googleapis.com/calendar/v3/calendars/'
            'calendar.user@example.com/events?key=google_api_key'
        )
        mock_post.assert_called_once()
        self.assertEqual(mock_post.call_args.args[0], expected_url)
        self.assertEqual(mock_post.call_args.kwargs['headers'], {
            'Authorization': 'Bearer google_user_token',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })

        payload = mock_post.call_args.kwargs['json']
        self.assertEqual(
            payload['summary'],
            'Project: Calendar project - Task: Calendar Task',
        )
        self.assertEqual(payload['start'], {'date': '2026-05-21'})
        self.assertEqual(payload['end'], {'date': '2026-05-21'})
        self.assertIn(
            {'email': 'assignee@example.com'}, payload['attendees'])
        self.assertIn(
            {'email': 'customer@example.com'}, payload['attendees'])
        self.assertEqual(task.task_event, 'google_event_1')
        self.assertEqual(task.task_created, 'calendar.user@example.com')

    @patch(
        'odoo.addons.sync_task_with_google_calender.models.'
        'project_task.requests.patch'
    )
    def test_write_task_updates_google_calendar_event(self, mock_patch):
        """Updating a synced task patches its Google Calendar event."""
        mock_patch.return_value = SimpleNamespace(status_code=200)
        task = self.env['project.task'].create({
            'name': 'Existing Calendar Task',
            'project_id': self.project.id,
            'partner_id': self.partner.id,
            'date_deadline': '2026-05-21',
            'task_event': 'google_event_2',
        })

        task.write({
            'name': 'Updated Calendar Task',
            'date_deadline': '2026-05-22',
        })

        expected_url = (
            'https://www.googleapis.com/calendar/v3/calendars/'
            'calendar.user@example.com/events/google_event_2'
            '?key=google_api_key'
        )
        mock_patch.assert_called_once()
        self.assertEqual(mock_patch.call_args.args[0], expected_url)
        payload = mock_patch.call_args.kwargs['json']
        self.assertEqual(payload['summary'], 'Updated Calendar Task')
        self.assertEqual(payload['start'], {'date': '2026-05-22'})
        self.assertEqual(payload['end'], {'date': '2026-05-22'})

    @patch(
        'odoo.addons.sync_task_with_google_calender.models.'
        'project_task.requests.delete'
    )
    def test_unlink_task_deletes_google_calendar_event(self, mock_delete):
        """Deleting a synced task deletes the related Google Calendar event."""
        mock_delete.return_value = SimpleNamespace(status_code=204)
        task = self.env['project.task'].create({
            'name': 'Delete Calendar Task',
            'project_id': self.project.id,
            'task_event': 'google_event_3',
        })

        task.unlink()

        mock_delete.assert_called_once_with(
            'https://www.googleapis.com/calendar/v3/calendars/'
            'calendar.user@example.com/events/google_event_3'
            '?key=google_api_key',
            headers={
                'Authorization': 'Bearer google_user_token',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
        )

    def test_create_task_requires_partner_and_deadline_for_sync(self):
        """Partner and deadline are required when Google sync is enabled."""
        with self.assertRaises(UserError):
            self.env['project.task'].create({
                'name': 'Incomplete Calendar Task',
                'project_id': self.project.id,
                'is_add_in_gcalendar': True,
            })
