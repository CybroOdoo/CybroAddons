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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestManagerApproval(TransactionCase):
    """Test suite for ManagerApproval model workflows, actions, and security."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_project_user = cls.env.ref('project.group_project_user')
        cls.group_project_manager = cls.env.ref(
            'project.group_project_manager'
        )

        cls.user_worker = cls.env['res.users'].create({
            'name': 'Approval Worker',
            'login': 'approval_worker_user',
            'email': 'approval_worker@example.com',
            'group_ids': [(6, 0, [cls.group_project_user.id])],
        })

        cls.user_assistant = cls.env['res.users'].create({
            'name': 'Assistant Worker',
            'login': 'assistant_worker_user',
            'email': 'assistant_worker@example.com',
            'group_ids': [(6, 0, [cls.group_project_user.id])],
        })

        cls.user_manager = cls.env['res.users'].create({
            'name': 'Approval Manager',
            'login': 'approval_manager_user',
            'email': 'approval_manager@example.com',
            'group_ids': [(6, 0, [
                cls.group_project_manager.id,
                cls.group_project_user.id,
            ])],
        })

        cls.project = cls.env['project.project'].create({
            'name': 'Manager Approval Project',
        })

        cls.task = cls.env['project.task'].create({
            'name': 'Manager Approval Target Task',
            'project_id': cls.project.id,
            'user_ids': [(6, 0, [cls.user_worker.id])],
            'allocated_hours': 12.0,
        })

    def test_01_user_security_access(self):
        """Test project users have read and create access on manager.approval."""
        task = self.task.with_user(self.user_worker)
        task.action_approval()

        # Regular worker can read manager.approval
        approvals = self.env['manager.approval'].with_user(
            self.user_worker
        ).search([('task_id', '=', task.id)])
        self.assertTrue(approvals)
        self.assertEqual(approvals.planned_hours, 12.0)

        # Manager has full access
        manager_approvals = self.env['manager.approval'].with_user(
            self.user_manager
        ).search([('task_id', '=', task.id)])
        self.assertEqual(approvals.ids, manager_approvals.ids)

    def test_02_action_approve_flow(self):
        """Test manager approving allocation request."""
        task = self.env['project.task'].create({
            'name': 'Approve Action Task',
            'project_id': self.project.id,
            'user_ids': [(6, 0, [self.user_worker.id])],
            'allocated_hours': 15.0,
        })
        task.action_approval()
        approval = task.manager_approval_id

        # Manager approves
        approval.with_user(self.user_manager).action_approve()

        self.assertTrue(approval.is_button_view)
        self.assertFalse(approval.is_button_view_cancel)
        self.assertEqual(task.allocated_hours, 15.0)

        progress_stage = task._get_project_stage("project.project_stage_1")
        if progress_stage:
            self.assertEqual(task.stage_id.id, progress_stage.id)

    def test_03_action_approve_with_modifications(self):
        """Test that modifying planned hours and assignees syncs back to task."""
        task = self.env['project.task'].create({
            'name': 'Adjusted Approval Task',
            'project_id': self.project.id,
            'user_ids': [(6, 0, [self.user_worker.id])],
            'allocated_hours': 20.0,
        })
        task.action_approval()
        approval = task.manager_approval_id

        # Manager adjusts planned hours and adds an assignee
        approval.with_user(self.user_manager).write({
            'planned_hours': 18.0,
            'user_ids': [(6, 0, [self.user_worker.id, self.user_assistant.id])],
        })
        approval.with_user(self.user_manager).action_approve()

        self.assertEqual(task.allocated_hours, 18.0)
        self.assertEqual(
            set(task.user_ids.ids),
            {self.user_worker.id, self.user_assistant.id},
        )

    def test_04_action_manager_cancel_flow(self):
        """Test manager cancelling allocation request."""
        task = self.env['project.task'].create({
            'name': 'Cancel Action Task',
            'project_id': self.project.id,
            'user_ids': [(6, 0, [self.user_worker.id])],
            'allocated_hours': 7.0,
        })
        task.action_approval()
        approval = task.manager_approval_id

        # Manager cancels
        approval.with_user(self.user_manager).action_manager_cancel()

        self.assertTrue(approval.is_button_view_cancel)
        self.assertFalse(approval.is_button_view)

        cancel_stage = task._get_project_stage("project.project_stage_3")
        if cancel_stage:
            self.assertEqual(task.stage_id.id, cancel_stage.id)

    def test_05_multi_record_approval_and_cancellation(self):
        """Test batch approve and cancel on manager.approval recordset."""
        t1 = self.env['project.task'].create({
            'name': 'Batch Approval Task 1',
            'project_id': self.project.id,
            'allocated_hours': 3.0,
        })
        t2 = self.env['project.task'].create({
            'name': 'Batch Approval Task 2',
            'project_id': self.project.id,
            'allocated_hours': 5.0,
        })
        tasks = t1 | t2
        tasks.action_approval()

        approvals = tasks.mapped('manager_approval_id')
        self.assertEqual(len(approvals), 2)

        # Batch approve
        approvals.with_user(self.user_manager).action_approve()
        self.assertTrue(all(a.is_button_view for a in approvals))
        self.assertEqual(t1.allocated_hours, 3.0)
        self.assertEqual(t2.allocated_hours, 5.0)

        # Batch cancel
        approvals.with_user(self.user_manager).action_manager_cancel()
        self.assertTrue(all(a.is_button_view_cancel for a in approvals))

    def test_06_stage_synchronization_from_task_write(self):
        """Test approval status synchronization when task stage is changed."""
        task = self.env['project.task'].create({
            'name': 'Sync Stage Task',
            'project_id': self.project.id,
            'allocated_hours': 6.0,
        })
        task.action_approval()
        approval = task.manager_approval_id

        stage_1 = task._get_project_stage("project.project_stage_1")
        stage_2 = task._get_project_stage("project.project_stage_2")
        stage_3 = task._get_project_stage("project.project_stage_3")

        # Moving to In Progress updates is_button_view
        if stage_1:
            task.with_user(self.user_manager).write({'stage_id': stage_1.id})
            self.assertTrue(approval.is_button_view)

        # Moving from In Progress to Done marks both buttons viewed
        if stage_2:
            task.with_user(self.user_manager).write({'stage_id': stage_2.id})
            self.assertTrue(approval.is_button_view)
            self.assertTrue(approval.is_button_view_cancel)
