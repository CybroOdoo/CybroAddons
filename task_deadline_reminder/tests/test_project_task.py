# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.info)
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
################################################################################
from odoo.tests.common import TransactionCase
from odoo import fields
from datetime import timedelta

class TestTaskDeadlineReminder(TransactionCase):
    """Test cases for the Task Deadline Reminder module."""

    def setUp(self):
        """Set up the test environment by creating test users and a project."""
        super().setUp()
        self.ProjectTask = self.env['project.task']
        self.User = self.env['res.users']
        
        # Create test users
        self.user_with_email = self.User.create({
            'name': 'User With Email',
            'login': 'user_email_test',
            'email': 'user@example.com',
        })
        
        # Create a test project
        self.project = self.env['project.project'].create({
            'name': 'Test Deadline Project'
        })

    def test_cron_deadline_reminder(self):
        """ Test the cron job sends reminder for today's deadline and ignores others. """
        
        # Task 1: Due today, reminder ON, user with email
        task_today = self.ProjectTask.create({
            'name': 'Task Today Email',
            'project_id': self.project.id,
            'user_ids': [(4, self.user_with_email.id)],
            'date_deadline': fields.Date.today(),
            'is_task_reminder': True,
        })
        
        # Task 2: Due tomorrow, reminder ON — should be ignored
        self.ProjectTask.create({
            'name': 'Task Tomorrow',
            'project_id': self.project.id,
            'user_ids': [(4, self.user_with_email.id)],
            'date_deadline': fields.Date.today() + timedelta(days=1),
            'is_task_reminder': True,
        })

        # Task 3: Due today, reminder OFF — should be ignored
        self.ProjectTask.create({
            'name': 'Task Today No Reminder',
            'project_id': self.project.id,
            'user_ids': [(4, self.user_with_email.id)],
            'date_deadline': fields.Date.today(),
            'is_task_reminder': False,
        })

        # Run the cron job method
        result = self.ProjectTask._cron_deadline_reminder()

        # Assert the cron returns True (completed without errors)
        self.assertTrue(result,
                        "Cron job should return True upon successful completion")

        # Assert that only task_today matched the reminder criteria
        reminded_tasks = self.ProjectTask.search([
            ('date_deadline', '!=', False),
            ('is_task_reminder', '=', True),
            ('user_ids', '!=', False),
        ])
        today_reminded = reminded_tasks.filtered(
            lambda t: t.date_deadline.date() == fields.Date.today()
        )
        self.assertEqual(len(today_reminded), 1,
                         "Only one task due today with reminder enabled should match")
        self.assertEqual(today_reminded.name, 'Task Today Email',
                         "The reminded task should be 'Task Today Email'")
