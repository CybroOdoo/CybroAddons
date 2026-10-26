# -*- coding: utf-8 -*-
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
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProjectTask(TransactionCase):
    """Test cases for 'project.task' model in volunteers_donors_management."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.volunteer_1 = cls.env['res.partner'].create({
            'name': 'Volunteer Alice',
            'email': 'alice@example.com',
            'is_volunteer': True,
        })
        cls.volunteer_2 = cls.env['res.partner'].create({
            'name': 'Volunteer Bob',
            'email': 'bob@example.com',
            'is_volunteer': True,
        })
        cls.assignee_user = cls.env['res.users'].create({
            'name': 'Task Assignee',
            'login': 'task_assignee_user',
            'email': 'assignee@example.com',
        })
        cls.project_manager_user = cls.env['res.users'].create({
            'name': 'Project Manager',
            'login': 'pm_user',
            'email': 'pm@example.com',
        })
        cls.project = cls.env['project.project'].create({
            'name': 'Community Service Project',
            'user_id': cls.project_manager_user.id,
            'project_partner_ids': [
                Command.link(cls.volunteer_1.id),
                Command.link(cls.volunteer_2.id),
            ],
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Relief Distribution Task',
            'project_id': cls.project.id,
            'user_ids': [Command.link(cls.assignee_user.id)],
        })

    def test_create_task_with_volunteers(self):
        """Test creating a task with volunteers automatically subscribes them."""
        task = self.env['project.task'].create({
            'name': 'New Task With Volunteers',
            'project_id': self.project.id,
            'project_task_partner_ids': [Command.link(self.volunteer_1.id)],
        })
        followers = task.message_follower_ids.mapped('partner_id')
        self.assertIn(self.volunteer_1, followers)

    def test_onchange_project_task_partner_ids(self):
        """Test onchange subscribes volunteers on an existing task, and runs safely on NewId."""
        # 1. Existing task
        self.task.project_task_partner_ids = [Command.set([self.volunteer_1.id])]
        self.task._onchange_project_task_partner_ids()
        followers = self.task.message_follower_ids.mapped('partner_id')
        self.assertIn(self.volunteer_1, followers)

        # 2. Unsaved draft (NewId) should not crash or attempt invalid DB subscribe
        new_task = self.env['project.task'].new({
            'name': 'Draft Task',
            'project_id': self.project.id,
            'project_task_partner_ids': [Command.set([self.volunteer_2.id])],
        })
        new_task._onchange_project_task_partner_ids()

    def test_write_and_follower_unsubscription(self):
        """Test write preserves followers on normal writes and only unsubscribes removed volunteers."""
        # Setup followers: project manager and assignee
        self.task.message_subscribe(partner_ids=[
            self.project_manager_user.partner_id.id,
            self.assignee_user.partner_id.id,
            self.volunteer_1.id,
            self.volunteer_2.id,
        ])
        self.task.write({
            'project_task_partner_ids': [Command.set([self.volunteer_1.id, self.volunteer_2.id])],
        })

        # 1. Normal field write should NOT unsubscribe anyone
        self.task.write({'name': 'Updated Relief Task Name'})
        followers = self.task.message_follower_ids.mapped('partner_id')
        self.assertIn(self.project_manager_user.partner_id, followers)
        self.assertIn(self.assignee_user.partner_id, followers)
        self.assertIn(self.volunteer_1, followers)
        self.assertIn(self.volunteer_2, followers)

        # 2. Removing volunteer_1 should unsubscribe volunteer_1, keeping others
        self.task.write({
            'project_task_partner_ids': [Command.set([self.volunteer_2.id])],
        })
        followers = self.task.message_follower_ids.mapped('partner_id')
        self.assertNotIn(self.volunteer_1, followers)
        self.assertIn(self.volunteer_2, followers)
        self.assertIn(self.project_manager_user.partner_id, followers)
        self.assertIn(self.assignee_user.partner_id, followers)

        # 3. If a volunteer is also an assignee, removing them as volunteer must not unsubscribe them
        self.volunteer_2.user_ids = [Command.link(self.assignee_user.id)]
        self.task.write({
            'project_task_partner_ids': [Command.set([])],
        })
        followers = self.task.message_follower_ids.mapped('partner_id')
        self.assertIn(self.assignee_user.partner_id, followers)
