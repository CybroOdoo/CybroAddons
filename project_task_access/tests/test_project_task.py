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
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestProjectTaskAccess(TransactionCase):
    """Test suite for ProjectTask access restrictions and compute fields."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = cls.env.ref('base.user_admin')
        cls.limited_access_group = cls.env.ref(
            'project_task_access.group_view_limited_projects_and_tasks'
        )

        # Create two test users with project user and limited access group
        groups = (
            'base.group_user,'
            'project.group_project_user,'
            'project_task_access.group_view_limited_projects_and_tasks'
        )
        cls.user_1 = new_test_user(
            cls.env,
            login='task_user_1',
            name='Task User 1',
            groups=groups,
        )
        cls.user_2 = new_test_user(
            cls.env,
            login='task_user_2',
            name='Task User 2',
            groups=groups,
        )
        cls.user_unrestricted = new_test_user(
            cls.env,
            login='task_user_unrestricted',
            name='Task User Unrestricted',
            groups='base.group_user,project.group_project_user',
        )

        # Create test projects
        cls.project_unrestricted = cls.env['project.project'].sudo().create({
            'name': 'Project Unrestricted',
            'project_access_user_ids': False,
        })
        cls.project_user_1_only = cls.env['project.project'].sudo().create({
            'name': 'Project User 1 Only',
            'project_access_user_ids': [Command.link(cls.user_1.id)],
        })

        # Create test tasks with sudo()
        cls.task_unrestricted = cls.env['project.task'].sudo().create({
            'name': 'Unrestricted Task',
            'project_id': cls.project_unrestricted.id,
            'task_access_user_ids': False,
        })
        cls.task_user_1_only = cls.env['project.task'].sudo().create({
            'name': 'User 1 Only Task',
            'project_id': cls.project_unrestricted.id,
            'task_access_user_ids': [Command.link(cls.user_1.id)],
        })
        cls.task_both_users = cls.env['project.task'].sudo().create({
            'name': 'Both Users Task',
            'project_id': cls.project_unrestricted.id,
            'task_access_user_ids': [
                Command.link(cls.user_1.id),
                Command.link(cls.user_2.id),
            ],
        })
        cls.task_in_restricted_project = cls.env['project.task'].sudo().create({
            'name': 'Task in Restricted Project',
            'project_id': cls.project_user_1_only.id,
            'task_access_user_ids': [Command.link(cls.user_1.id)],
        })

    def test_is_internal_user_admin(self):
        """Verify is_internal_user computes to True for admin user."""
        task = self.task_unrestricted.with_user(self.admin_user)
        self.assertTrue(
            task.is_internal_user,
            "is_internal_user should be True for admin user.",
        )

    def test_is_internal_user_non_admin(self):
        """Verify is_internal_user computes to False for non-admin user."""
        task = self.task_unrestricted.with_user(self.user_1)
        self.assertFalse(
            task.is_internal_user,
            "is_internal_user should be False for non-admin user.",
        )

    def test_task_access_unrestricted(self):
        """Unrestricted task should be visible to any user in the group."""
        tasks_user_1 = self.env['project.task'].with_user(self.user_1).search([
            ('id', '=', self.task_unrestricted.id)
        ])
        self.assertIn(
            self.task_unrestricted,
            tasks_user_1,
            "User 1 should have access to unrestricted task.",
        )

        tasks_user_2 = self.env['project.task'].with_user(self.user_2).search([
            ('id', '=', self.task_unrestricted.id)
        ])
        self.assertIn(
            self.task_unrestricted,
            tasks_user_2,
            "User 2 should have access to unrestricted task.",
        )

    def test_task_access_restricted(self):
        """Task restricted to user_1 is visible to user_1, not user_2."""
        tasks_user_1 = self.env['project.task'].with_user(self.user_1).search([
            ('id', '=', self.task_user_1_only.id)
        ])
        self.assertIn(
            self.task_user_1_only,
            tasks_user_1,
            "User 1 should see the task they have access to.",
        )

        tasks_user_2 = self.env['project.task'].with_user(self.user_2).search([
            ('id', '=', self.task_user_1_only.id)
        ])
        self.assertNotIn(
            self.task_user_1_only,
            tasks_user_2,
            "User 2 should not see the task restricted to User 1.",
        )

        # Attempting direct read by unauthorized user should raise AccessError
        with self.assertRaises(AccessError):
            self.task_user_1_only.with_user(self.user_2).read(['name'])

    def test_task_in_restricted_project(self):
        """Task within a restricted project is accessible to user_1 and not user_2."""
        tasks_user_1 = self.env['project.task'].with_user(self.user_1).search([
            ('id', '=', self.task_in_restricted_project.id)
        ])
        self.assertIn(
            self.task_in_restricted_project,
            tasks_user_1,
            "User 1 should see the task in restricted project.",
        )

        tasks_user_2 = self.env['project.task'].with_user(self.user_2).search([
            ('id', '=', self.task_in_restricted_project.id)
        ])
        self.assertNotIn(
            self.task_in_restricted_project,
            tasks_user_2,
            "User 2 should not see the task in project restricted to User 1.",
        )

        with self.assertRaises(AccessError):
            self.task_in_restricted_project.with_user(self.user_2).read(['name'])

    def test_task_access_multiple_users(self):
        """Task assigned to multiple users is accessible to all assigned users."""
        tasks_user_1 = self.env['project.task'].with_user(self.user_1).search([
            ('id', '=', self.task_both_users.id)
        ])
        self.assertIn(
            self.task_both_users,
            tasks_user_1,
            "User 1 should see the task assigned to multiple users.",
        )

        tasks_user_2 = self.env['project.task'].with_user(self.user_2).search([
            ('id', '=', self.task_both_users.id)
        ])
        self.assertIn(
            self.task_both_users,
            tasks_user_2,
            "User 2 should see the task assigned to multiple users.",
        )

    def test_task_access_assignment_update(self):
        """Adding a user grants access, removing a user revokes access."""
        task = self.env['project.task'].sudo().create({
            'name': 'Dynamic Access Task',
            'project_id': self.project_unrestricted.id,
            'task_access_user_ids': [Command.link(self.user_1.id)],
        })
        # User 2 has no access initially
        search_res = self.env['project.task'].with_user(self.user_2).search([
            ('id', '=', task.id),
        ])
        self.assertNotIn(task, search_res)

        # Add User 2
        task.sudo().write({
            'task_access_user_ids': [Command.link(self.user_2.id)],
        })
        search_res = self.env['project.task'].with_user(self.user_2).search([
            ('id', '=', task.id),
        ])
        self.assertIn(task, search_res)

        # Remove User 1
        task.sudo().write({
            'task_access_user_ids': [Command.unlink(self.user_1.id)],
        })
        search_res = self.env['project.task'].with_user(self.user_1).search([
            ('id', '=', task.id),
        ])
        self.assertNotIn(task, search_res)

    def test_task_access_user_ids_admin_only_write(self):
        """Verify non-admin user cannot modify task_access_user_ids."""
        task = self.task_unrestricted.with_user(self.user_1)
        with self.assertRaises(AccessError):
            task.write({
                'task_access_user_ids': [Command.link(self.user_1.id)],
            })

    def test_task_access_user_ids_admin_only_create(self):
        """Verify non-admin user cannot set task_access_user_ids on creation."""
        with self.assertRaises(AccessError):
            self.env['project.task'].with_user(self.user_1).create({
                'name': 'Unauthorized Creation Task',
                'project_id': self.project_unrestricted.id,
                'task_access_user_ids': [Command.link(self.user_1.id)],
            })

    def test_unrestricted_user_without_restriction_group(self):
        """User without limited access group can see tasks regardless of access list."""
        tasks = self.env['project.task'].with_user(self.user_unrestricted).search([
            ('id', '=', self.task_user_1_only.id),
        ])
        self.assertIn(
            self.task_user_1_only,
            tasks,
            "User without restriction group should not be restricted by this module's rule.",
        )

    def test_admin_can_write_task_access_user_ids(self):
        """Admin user can modify task_access_user_ids freely."""
        task = self.task_unrestricted.with_user(self.admin_user)
        task.write({
            'task_access_user_ids': [Command.link(self.user_1.id)],
        })
        self.assertIn(self.user_1, task.task_access_user_ids)

    def test_admin_can_create_task_with_access_user_ids(self):
        """Admin user can create a task with task_access_user_ids."""
        task = self.env['project.task'].with_user(self.admin_user).create({
            'name': 'Admin Created Restricted Task',
            'project_id': self.project_unrestricted.id,
            'task_access_user_ids': [Command.link(self.user_2.id)],
        })
        self.assertIn(self.user_2, task.task_access_user_ids)

    def test_clearing_task_access_user_ids(self):
        """Clearing task_access_user_ids makes task unrestricted again."""
        task = self.task_user_1_only.with_user(self.admin_user)
        task.write({'task_access_user_ids': [Command.clear()]})
        self.assertFalse(task.task_access_user_ids)

        tasks_user_2 = self.env['project.task'].with_user(self.user_2).search([
            ('id', '=', task.id),
        ])
        self.assertIn(
            task,
            tasks_user_2,
            "After clearing restrictions, user 2 can view the task.",
        )

    def test_non_admin_can_write_other_fields(self):
        """Permitted non-admin user can edit normal task fields without error."""
        task = self.task_both_users.with_user(self.user_1)
        task.write({'description': '<p>Updated task details</p>'})
        self.assertIn('Updated task details', str(task.description))

        # But attempting to write task_access_user_ids raises AccessError
        with self.assertRaises(AccessError):
            task.write({
                'task_access_user_ids': [Command.link(self.user_1.id)],
            })

    def test_core_task_rules_not_tampered(self):
        """Verify that core task rule metadata is not permanently set to noupdate."""
        for xml_name in ['task_visibility_rule', 'ir_rule_private_task', 'project_manager_all_project_tasks_rule']:
            data = self.env['ir.model.data'].search([
                ('module', '=', 'project'),
                ('name', '=', xml_name),
            ])
            if data:
                self.assertFalse(
                    data.noupdate,
                    f"Core task rule project.{xml_name} should have noupdate=False.",
                )
