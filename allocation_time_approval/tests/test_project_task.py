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
from odoo.exceptions import UserError, ValidationError


@tagged('post_install', '-at_install')
class TestProjectTask(TransactionCase):
    """Test suite for ProjectTask approval workflows, permissions, and guards."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_project_user = cls.env.ref('project.group_project_user')
        cls.group_project_manager = cls.env.ref(
            'project.group_project_manager'
        )

        cls.user_worker = cls.env['res.users'].create({
            'name': 'Task Worker',
            'login': 'task_worker_user',
            'email': 'task_worker@example.com',
            'group_ids': [(6, 0, [cls.group_project_user.id])],
        })

        cls.user_manager = cls.env['res.users'].create({
            'name': 'Task Project Manager',
            'login': 'task_manager_user',
            'email': 'task_manager@example.com',
            'group_ids': [(6, 0, [
                cls.group_project_manager.id,
                cls.group_project_user.id,
            ])],
        })

        cls.project = cls.env['project.project'].create({
            'name': 'Project Task Approval Test',
        })

        cls.task = cls.env['project.task'].create({
            'name': 'Approval Flow Task',
            'project_id': cls.project.id,
            'user_ids': [(6, 0, [cls.user_worker.id])],
            'allocated_hours': 8.0,
        })

    def test_01_task_creation_and_stage_computes(self):
        """Test initial state and compute flags upon task creation."""
        task = self.task
        self.assertTrue(task.is_new_stage)
        self.assertFalse(task.is_approve_stage)
        self.assertFalse(task.is_progress_stage)
        self.assertEqual(task.allocated_hours, 8.0)

    def test_02_action_approval_submission(self):
        """Test submitting task for manager approval via action_approval."""
        task = self.task.with_user(self.user_worker)
        task.action_approval()

        to_approve_stage = task._get_to_approve_stage()
        if to_approve_stage:
            self.assertEqual(task.stage_id.id, to_approve_stage.id)
        self.assertTrue(task.is_approve_stage)
        self.assertFalse(task.is_new_stage)
        self.assertEqual(task.allocated_hours, 0.0)

        approval = task.manager_approval_id
        self.assertTrue(approval)
        self.assertEqual(approval.task_id.id, task.id)
        self.assertEqual(approval.planned_hours, 8.0)
        self.assertEqual(approval.project_id.id, self.project.id)
        self.assertIn(self.user_worker.id, approval.user_ids.ids)

    def test_03_stage_transition_permissions_worker(self):
        """Test that standard project users cannot make unauthorized stage moves."""
        task = self.env['project.task'].create({
            'name': 'Permission Test Task',
            'project_id': self.project.id,
            'allocated_hours': 4.0,
        })
        task.action_approval()
        to_approve_stage = task._get_to_approve_stage()
        stage_0 = task._get_project_stage("project.project_stage_0")
        stage_1 = task._get_project_stage("project.project_stage_1")

        worker_task = task.with_user(self.user_worker)

        # Worker cannot move out of To Approve stage
        if stage_1 and to_approve_stage:
            with self.assertRaises(ValidationError):
                worker_task.write({'stage_id': stage_1.id})

        # Worker cannot move directly to initial stage_0
        if stage_0:
            with self.assertRaises(ValidationError):
                worker_task.write({'stage_id': stage_0.id})

    def test_04_completed_task_cannot_move_back_to_approve(self):
        """Test that managers cannot move completed tasks back to To Approve."""
        task = self.env['project.task'].create({
            'name': 'Completed Guard Task',
            'project_id': self.project.id,
            'allocated_hours': 2.0,
        })
        stage_2 = task._get_project_stage("project.project_stage_2")
        to_approve_stage = task._get_to_approve_stage()

        if stage_2 and to_approve_stage:
            task.with_user(self.user_manager).write({'stage_id': stage_2.id})
            with self.assertRaises(ValidationError):
                task.with_user(self.user_manager).write({
                    'stage_id': to_approve_stage.id,
                })

    def test_05_action_done_over_allocation_guard(self):
        """Test overtime guard blocks non-managers but allows managers on Done."""
        task = self.env['project.task'].create({
            'name': 'Overtime Task',
            'project_id': self.project.id,
            'user_ids': [(6, 0, [self.user_worker.id])],
            'allocated_hours': 5.0,
        })
        task.action_approval()
        task.manager_approval_id.with_user(self.user_manager).action_approve()

        # Simulate logged timesheet hours exceeding allocation
        if 'account.analytic.line' in self.env:
            employee = self.env['hr.employee'].sudo().create({
                'name': 'Overtime Employee',
                'user_id': self.user_worker.id,
            })
            self.env['account.analytic.line'].sudo().create({
                'name': 'Extra Work Timesheet',
                'task_id': task.id,
                'project_id': self.project.id,
                'employee_id': employee.id,
                'user_id': self.user_worker.id,
                'unit_amount': 10.0,
            })

        if task.effective_hours > task.allocated_hours:
            with self.assertRaises(UserError):
                task.with_user(self.user_worker).action_done()

            # Manager can authorize and mark as Done
            task.with_user(self.user_manager).action_done()
            done_stage = task._get_project_stage("project.project_stage_2")
            if done_stage:
                self.assertEqual(task.stage_id.id, done_stage.id)

    def test_06_action_done_within_allocation(self):
        """Test that tasks within allocated hours can be marked Done by workers."""
        task = self.env['project.task'].create({
            'name': 'Normal Completion Task',
            'project_id': self.project.id,
            'user_ids': [(6, 0, [self.user_worker.id])],
            'allocated_hours': 10.0,
        })
        task.action_approval()
        task.manager_approval_id.with_user(self.user_manager).action_approve()

        # Worker calls action_done within budget
        task.with_user(self.user_worker).action_done()
        done_stage = task._get_project_stage("project.project_stage_2")
        if done_stage:
            self.assertEqual(task.stage_id.id, done_stage.id)

    def test_07_action_cancel(self):
        """Test cancelling task through action_cancel."""
        task = self.env['project.task'].create({
            'name': 'Cancel Flow Task',
            'project_id': self.project.id,
            'allocated_hours': 3.0,
        })
        task.action_cancel()
        cancel_stage = task._get_project_stage("project.project_stage_3")
        if cancel_stage:
            self.assertEqual(task.stage_id.id, cancel_stage.id)

    def test_08_batch_operations_no_singleton_error(self):
        """Test batch approval submission and multi-record writes."""
        t1 = self.env['project.task'].create({
            'name': 'Batch Task A',
            'project_id': self.project.id,
            'allocated_hours': 4.0,
        })
        t2 = self.env['project.task'].create({
            'name': 'Batch Task B',
            'project_id': self.project.id,
            'allocated_hours': 6.0,
        })
        tasks = t1 | t2
        tasks.action_approval()
        self.assertTrue(all(t.is_approve_stage for t in tasks))

        # Batch write does not raise Expected singleton
        tasks.write({'priority': '1'})
        self.assertEqual(tasks.mapped('priority'), ['1', '1'])

    def test_09_read_and_computes_no_side_effects(self):
        """Test that reading tasks and computing flags does not modify stages."""
        stage_count_before = self.env['project.task.type'].search_count([])

        t = self.env['project.task'].create({
            'name': 'Side Effect Free Task',
            'project_id': self.project.id,
            'allocated_hours': 5.0,
        })
        _ = t.read(['is_new_stage', 'is_approve_stage', 'is_progress_stage'])

        stage_count_after = self.env['project.task.type'].search_count([])
        self.assertEqual(stage_count_before, stage_count_after)
