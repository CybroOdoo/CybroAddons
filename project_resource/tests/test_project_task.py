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
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProjectResourcePortal(TransactionCase):

    @classmethod
    def setUpClass(cls):
        """Create portal project and test users for portal resource access."""
        super().setUpClass()

        project_vals = {
            'name': 'Portal Project',
            'privacy_visibility': 'portal',
        }
        if 'billing_type' in cls.env['project.project']._fields:
            project_vals['billing_type'] = 'not_billable'
        cls.project_portal = cls.env['project.project'].create(project_vals)

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

        cls.project_portal.message_subscribe(
            partner_ids=[cls.portal_user.partner_id.id]
        )

    def test_portal_user_visibility_task(self):
        """Test portal follower is in task's computed users_ids."""
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

        task._compute_users_ids()

        self.assertIn(self.internal_user, task.users_ids)
        self.assertIn(self.portal_user, task.users_ids)
        self.assertNotIn(other_portal_user, task.users_ids)

    def test_portal_user_visibility_wizard(self):
        """Test Free Resource wizard returns followed portal user."""
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

        # Search users using the domain returned by the wizard
        allowed_users = self.env['res.users'].search(domain)

        self.assertIn(self.portal_user, allowed_users)
        self.assertIn(self.internal_user, allowed_users)
        self.assertNotIn(other_portal_user, allowed_users)

    def test_deadline_before_start_date_raises(self):
        """Test deadline before task start date raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.env['project.task'].create({
                'name': 'Invalid Date Task',
                'project_id': self.project_portal.id,
                'task_start_date': fields.Date.to_date('2026-06-15'),
                'date_deadline': fields.Date.to_date('2026-06-10'),
            })

    def test_assignee_availability_constraint(self):
        """Test assigning busy user raises ValidationError."""
        self.env['project.task'].create({
            'name': 'Task A',
            'project_id': self.project_portal.id,
            'task_start_date': fields.Date.to_date('2026-06-10'),
            'date_deadline': fields.Date.to_date('2026-06-20'),
            'user_ids': [(6, 0, [self.internal_user.id])],
        })

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
        self.env['project.task'].create({
            'name': 'Task A',
            'project_id': self.project_portal.id,
            'task_start_date': fields.Date.to_date('2026-06-10'),
            'date_deadline': fields.Date.to_date('2026-06-20'),
            'user_ids': [(6, 0, [self.internal_user.id])],
        })

        # Verify get_free_resource_ids for June 20 to June 25
        busy_ids = self.env['project.task'].get_free_resource_ids(
            fields.Date.to_date('2026-06-20'),
            fields.Date.to_date('2026-06-25'),
        )
        self.assertIn(self.internal_user.id, busy_ids)

        busy_ids_2 = self.env['project.task'].get_free_resource_ids(
            fields.Date.to_date('2026-06-05'),
            fields.Date.to_date('2026-06-10'),
        )
        self.assertIn(self.internal_user.id, busy_ids_2)

        busy_ids_3 = self.env['project.task'].get_free_resource_ids(
            fields.Date.to_date('2026-06-01'),
            fields.Date.to_date('2026-06-09'),
        )
        self.assertNotIn(self.internal_user.id, busy_ids_3)
