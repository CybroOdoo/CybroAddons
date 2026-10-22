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
class TestProjectProjectAccess(TransactionCase):
    """Test suite for ProjectProject access restrictions and compute fields."""

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
            login='project_user_1',
            name='Project User 1',
            groups=groups,
        )
        cls.user_2 = new_test_user(
            cls.env,
            login='project_user_2',
            name='Project User 2',
            groups=groups,
        )
        cls.user_unrestricted = new_test_user(
            cls.env,
            login='project_user_unrestricted',
            name='Project User Unrestricted',
            groups='base.group_user,project.group_project_user',
        )
        cls.user_manager = new_test_user(
            cls.env,
            login='project_manager_limited',
            name='Project Manager Limited',
            groups=(
                'base.group_user,'
                'project.group_project_manager,'
                'project_task_access.group_view_limited_projects_and_tasks'
            ),
        )

        # Create test projects with sudo()
        cls.project_unrestricted = cls.env['project.project'].sudo().create({
            'name': 'Unrestricted Project',
            'project_access_user_ids': False,
        })
        cls.project_user_1_only = cls.env['project.project'].sudo().create({
            'name': 'User 1 Only Project',
            'project_access_user_ids': [Command.link(cls.user_1.id)],
        })
        cls.project_both_users = cls.env['project.project'].sudo().create({
            'name': 'Both Users Project',
            'project_access_user_ids': [
                Command.link(cls.user_1.id),
                Command.link(cls.user_2.id),
            ],
        })

    def test_is_internal_user_admin(self):
        """Verify is_internal_user computes to True for admin user."""
        project = self.project_unrestricted.with_user(self.admin_user)
        self.assertTrue(
            project.is_internal_user,
            "is_internal_user should be True for admin user.",
        )

    def test_is_internal_user_non_admin(self):
        """Verify is_internal_user computes to False for non-admin user."""
        project = self.project_unrestricted.with_user(self.user_1)
        self.assertFalse(
            project.is_internal_user,
            "is_internal_user should be False for non-admin user.",
        )

    def test_project_access_unrestricted(self):
        """Unrestricted project should be visible to any user in the group."""
        projects_user_1 = self.env['project.project'].with_user(self.user_1).search([
            ('id', '=', self.project_unrestricted.id)
        ])
        self.assertIn(
            self.project_unrestricted,
            projects_user_1,
            "User 1 should have access to unrestricted project.",
        )

        projects_user_2 = self.env['project.project'].with_user(self.user_2).search([
            ('id', '=', self.project_unrestricted.id)
        ])
        self.assertIn(
            self.project_unrestricted,
            projects_user_2,
            "User 2 should have access to unrestricted project.",
        )

    def test_project_access_restricted(self):
        """Project restricted to user_1 is visible to user_1, not user_2."""
        projects_user_1 = self.env['project.project'].with_user(self.user_1).search([
            ('id', '=', self.project_user_1_only.id)
        ])
        self.assertIn(
            self.project_user_1_only,
            projects_user_1,
            "User 1 should see the project they have access to.",
        )

        projects_user_2 = self.env['project.project'].with_user(self.user_2).search([
            ('id', '=', self.project_user_1_only.id)
        ])
        self.assertNotIn(
            self.project_user_1_only,
            projects_user_2,
            "User 2 should not see the project restricted to User 1.",
        )

        # Attempting direct read by unauthorized user should raise AccessError
        with self.assertRaises(AccessError):
            self.project_user_1_only.with_user(self.user_2).read(['name'])

    def test_project_access_multiple_users(self):
        """Project assigned to multiple users is accessible to all assigned users."""
        projects_user_1 = self.env['project.project'].with_user(self.user_1).search([
            ('id', '=', self.project_both_users.id)
        ])
        self.assertIn(
            self.project_both_users,
            projects_user_1,
            "User 1 should see the project assigned to multiple users.",
        )

        projects_user_2 = self.env['project.project'].with_user(self.user_2).search([
            ('id', '=', self.project_both_users.id)
        ])
        self.assertIn(
            self.project_both_users,
            projects_user_2,
            "User 2 should see the project assigned to multiple users.",
        )

    def test_project_access_assignment_update(self):
        """Adding a user grants access, removing a user revokes access."""
        project = self.env['project.project'].sudo().create({
            'name': 'Dynamic Access Project',
            'project_access_user_ids': [Command.link(self.user_1.id)],
        })
        # User 2 has no access initially
        search_res = self.env['project.project'].with_user(self.user_2).search([
            ('id', '=', project.id),
        ])
        self.assertNotIn(project, search_res)

        # Add User 2
        project.sudo().write({
            'project_access_user_ids': [Command.link(self.user_2.id)],
        })
        search_res = self.env['project.project'].with_user(self.user_2).search([
            ('id', '=', project.id),
        ])
        self.assertIn(project, search_res)

        # Remove User 1
        project.sudo().write({
            'project_access_user_ids': [Command.unlink(self.user_1.id)],
        })
        search_res = self.env['project.project'].with_user(self.user_1).search([
            ('id', '=', project.id),
        ])
        self.assertNotIn(project, search_res)

    def test_project_access_user_ids_admin_only_write(self):
        """Verify non-admin user cannot modify project_access_user_ids."""
        project = self.project_unrestricted.with_user(self.user_1)
        with self.assertRaises(AccessError):
            project.write({
                'project_access_user_ids': [Command.link(self.user_1.id)],
            })

    def test_project_access_user_ids_admin_only_create(self):
        """Verify non-admin user cannot set project_access_user_ids on creation."""
        with self.assertRaises(AccessError):
            self.env['project.project'].with_user(self.user_1).create({
                'name': 'Unauthorized Creation Project',
                'project_access_user_ids': [Command.link(self.user_1.id)],
            })

    def test_unrestricted_user_without_restriction_group(self):
        """User without limited access group can see projects regardless of access list."""
        projects = self.env['project.project'].with_user(self.user_unrestricted).search([
            ('id', '=', self.project_user_1_only.id),
        ])
        self.assertIn(
            self.project_user_1_only,
            projects,
            "User without restriction group should not be restricted by this module's rule.",
        )

    def test_admin_can_write_project_access_user_ids(self):
        """Admin user can modify project_access_user_ids freely."""
        project = self.project_unrestricted.with_user(self.admin_user)
        project.write({
            'project_access_user_ids': [Command.link(self.user_1.id)],
        })
        self.assertIn(self.user_1, project.project_access_user_ids)

    def test_admin_can_create_project_with_access_user_ids(self):
        """Admin user can create a project with project_access_user_ids."""
        project = self.env['project.project'].with_user(self.admin_user).create({
            'name': 'Admin Created Restricted Project',
            'project_access_user_ids': [Command.link(self.user_2.id)],
        })
        self.assertIn(self.user_2, project.project_access_user_ids)

    def test_clearing_project_access_user_ids(self):
        """Clearing project_access_user_ids makes project unrestricted again."""
        project = self.project_user_1_only.with_user(self.admin_user)
        project.write({'project_access_user_ids': [Command.clear()]})
        self.assertFalse(project.project_access_user_ids)

        projects_user_2 = self.env['project.project'].with_user(self.user_2).search([
            ('id', '=', project.id),
        ])
        self.assertIn(
            project,
            projects_user_2,
            "After clearing restrictions, user 2 can view the project.",
        )

    def test_non_admin_can_write_other_fields(self):
        """Non-admin project manager can edit normal fields without triggering check."""
        project = self.project_unrestricted.with_user(self.user_manager)
        project.write({'name': 'Renamed by Manager'})
        self.assertEqual(project.name, 'Renamed by Manager')

        # But attempting to write project_access_user_ids raises AccessError
        with self.assertRaises(AccessError):
            project.write({
                'project_access_user_ids': [Command.link(self.user_1.id)],
            })

    def test_core_project_rule_not_tampered(self):
        """Verify that core project rule metadata is not permanently set to noupdate."""
        data = self.env['ir.model.data'].search([
            ('module', '=', 'project'),
            ('name', '=', 'project_public_members_rule'),
        ])
        if data:
            self.assertFalse(
                data.noupdate,
                "Core project rule should have noupdate=False.",
            )
