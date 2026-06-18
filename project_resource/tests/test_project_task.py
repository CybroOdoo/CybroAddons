# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase
from odoo import fields


class TestProjectResourcePortal(TransactionCase):

    def setUp(self):
        """Initialize the test environment before each test case."""
        super().setUp()

    @classmethod
    def setUpClass(cls):
        """Create a portal project and test users for portal resource access validation."""
        super(TestProjectResourcePortal, cls).setUpClass()
        
        # Create a project with portal visibility
        project_vals = {
            'name': 'Portal Project',
            'privacy_visibility': 'portal',
        }
        if 'billing_type' in cls.env['project.project']._fields:
            project_vals['billing_type'] = 'not_billable'
        cls.project_portal = cls.env['project.project'].create(project_vals)
        
        # Create internal user and portal user
        cls.internal_user = cls.env['res.users'].create({
            'name': 'Internal Employee',
            'login': 'employee_internal',
            'email': 'internal@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal Customer',
            'login': 'customer_portal',
            'email': 'portal@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        
        # Follow project with portal user
        cls.project_portal.message_subscribe(partner_ids=[cls.portal_user.partner_id.id])

    def test_portal_user_visibility_task(self):
        """Test that portal follower is in task's computed users_ids, but non-follower portal user is not."""
        # Create another portal user who does NOT follow the project
        other_portal_user = self.env['res.users'].create({
            'name': 'Other Portal Customer',
            'login': 'customer_portal_other',
            'email': 'portal_other@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        task = self.env['project.task'].create({
            'name': 'Portal Task',
            'project_id': self.project_portal.id,
        })

        # Trigger compute
        task._compute_users_ids()

        # The project followers (internal_user if follows, and portal_user)
        # and all internal users (since privacy_visibility = 'portal') should be visible.
        # internal_user is share=False, so they must be in task.users_ids
        # portal_user is a follower and portal visibility is active, so they must be in task.users_ids
        # other_portal_user is share=True but NOT a follower, so they must NOT be in task.users_ids
        self.assertIn(self.internal_user, task.users_ids)
        self.assertIn(self.portal_user, task.users_ids)
        self.assertNotIn(other_portal_user, task.users_ids)

    def test_portal_user_visibility_wizard(self):
        """Test that the Free Resource wizard returns the followed portal user but not other portal users."""
        other_portal_user = self.env['res.users'].create({
            'name': 'Other Portal Customer 2',
            'login': 'customer_portal_other_2',
            'email': 'portal_other2@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        
        wizard = self.env['free.resource'].create({
            'date_from': fields.Date.to_date('2026-06-01'),
            'date_to': fields.Date.to_date('2026-06-30'),
        })
        
        action = wizard.get_free_resource()
        domain = action.get('domain', [])
        
        # Let's search using the domain returned by the wizard
        allowed_users = self.env['res.users'].search(domain)
        
        # portal_user must be in allowed_users because they follow a project
        self.assertIn(self.portal_user, allowed_users)
        self.assertIn(self.internal_user, allowed_users)
        # other_portal_user is not a follower, collaborator, or assignee, so they should not be in allowed_users
        self.assertNotIn(other_portal_user, allowed_users)

    def test_deadline_before_start_date_raises(self):
        """Test that setting a deadline before the task start date raises a ValidationError."""
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.env['project.task'].create({
                'name': 'Invalid Date Task',
                'project_id': self.project_portal.id,
                'task_start_date': fields.Date.to_date('2026-06-15'),
                'date_deadline': fields.Date.to_date('2026-06-10'),
            })

    def test_assignee_availability_constraint(self):
        """Test that assigning a busy user to a new/modified task raises ValidationError."""
        from odoo.exceptions import ValidationError
        
        # Create Task A for internal_user from June 10 to June 20
        self.env['project.task'].create({
            'name': 'Task A',
            'project_id': self.project_portal.id,
            'task_start_date': fields.Date.to_date('2026-06-10'),
            'date_deadline': fields.Date.to_date('2026-06-20'),
            'user_ids': [(6, 0, [self.internal_user.id])],
        })

        # Try to create Task B for internal_user that overlaps (June 15 to June 25) - should fail
        with self.assertRaises(ValidationError):
            self.env['project.task'].create({
                'name': 'Task B',
                'project_id': self.project_portal.id,
                'task_start_date': fields.Date.to_date('2026-06-15'),
                'date_deadline': fields.Date.to_date('2026-06-25'),
                'user_ids': [(6, 0, [self.internal_user.id])],
            })

    def test_overlap_boundary_conditions(self):
        """Test boundary cases for overlapping date ranges."""
        # Task A from June 10 to June 20
        task_a = self.env['project.task'].create({
            'name': 'Task A',
            'project_id': self.project_portal.id,
            'task_start_date': fields.Date.to_date('2026-06-10'),
            'date_deadline': fields.Date.to_date('2026-06-20'),
            'user_ids': [(6, 0, [self.internal_user.id])],
        })

        # Case 1: Start date matches existing end date (June 20).
        # Depending on business rule, touching dates might be considered busy or free.
        # Let's verify what get_free_resource_ids does for June 20 to June 25.
        busy_ids = self.env['project.task'].get_free_resource_ids(
            fields.Date.to_date('2026-06-20'),
            fields.Date.to_date('2026-06-25')
        )
        self.assertIn(self.internal_user.id, busy_ids)

        # Case 2: End date matches existing start date (June 10)
        busy_ids_2 = self.env['project.task'].get_free_resource_ids(
            fields.Date.to_date('2026-06-05'),
            fields.Date.to_date('2026-06-10')
        )
        self.assertIn(self.internal_user.id, busy_ids_2)

        # Case 3: Completely outside (June 1st to June 9th)
        busy_ids_3 = self.env['project.task'].get_free_resource_ids(
            fields.Date.to_date('2026-06-01'),
            fields.Date.to_date('2026-06-09')
        )
        self.assertNotIn(self.internal_user.id, busy_ids_3)
