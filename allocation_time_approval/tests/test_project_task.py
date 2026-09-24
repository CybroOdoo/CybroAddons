# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhil Ashok(odoo@cybrosys.com)
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
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestProjectTask(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestProjectTask, cls).setUpClass()
        # Create user groups if not assigned
        group_manager = cls.env.ref('project.group_project_manager')
        group_user = cls.env.ref('project.group_project_user')
        group_employee = cls.env.ref('base.group_user')

        # Setup users
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Manager User',
            'login': 'manager_user',
            'email': 'manager@example.com',
            'groups_id': [(6, 0, [group_manager.id, group_employee.id])]
        })
        
        cls.user_assignee = cls.env['res.users'].create({
            'name': 'Assignee User',
            'login': 'assignee_user',
            'email': 'assignee@example.com',
            'groups_id': [(6, 0, [group_user.id, group_employee.id])]
        })

        # Get stages
        cls.stage_new = cls.env.ref("project.project_stage_0", raise_if_not_found=False)
        if not cls.stage_new:
            cls.stage_new = cls.env['project.task.type'].search([], order='sequence asc', limit=1)
        cls.stage_to_approve = cls.env.ref("allocation_time_approval.task_type_to_approve")
        cls.stage_in_progress = cls.env.ref("project.project_stage_1", raise_if_not_found=False)
        cls.stage_done = cls.env.ref("project.project_stage_2", raise_if_not_found=False)
        cls.stage_cancelled = cls.env.ref("project.project_stage_3", raise_if_not_found=False)

        # Create a Project
        cls.project = cls.env['project.project'].create({
            'name': 'Test Project',
            'privacy_visibility': 'employees'
        })
        
        # Create a Task
        cls.task = cls.env['project.task'].with_user(cls.user_manager).create({
            'name': 'Test Task',
            'project_id': cls.project.id,
            'user_ids': [(4, cls.user_assignee.id)],
            'allocated_hours': 10.0,
            'stage_id': cls.stage_new.id if cls.stage_new else False
        })

    def test_01_compute_stages_and_admin(self):
        """Test compute fields for stages and administrator access"""
        self.task.with_user(self.user_manager)._compute_is_administrator()
        self.assertTrue(self.task.is_administrator, "Manager should be admin")
        
        self.task.with_user(self.user_assignee)._compute_is_administrator()
        self.assertFalse(self.task.is_administrator, "Assignee should not be admin")
        
        self.assertTrue(self.task.new_stage, "Task should be in new stage")
        self.assertFalse(self.task.to_approve_stage)
        self.assertFalse(self.task.to_progress_stage)

    def test_02_action_approval(self):
        """Test request approval action creates manager approval and changes stage"""
        self.task.with_user(self.user_assignee).action_approval()
        self.assertEqual(self.task.stage_id.id, self.stage_to_approve.id if self.stage_to_approve else False)
        self.assertFalse(self.task.task_create_boolean)
        self.assertEqual(self.task.allocated_hours, 0)
        
        approval_rec = self.env['manager.approval'].search([('task_id', '=', self.task.id)])
        self.assertTrue(approval_rec)

    def test_03_write_restrictions_non_manager(self):
        """Test stage transition restrictions for regular users"""
        with self.assertRaises(ValidationError, msg="Only Managers can perform this move!"):
            self.task.with_user(self.user_assignee).write({'stage_id': self.stage_done.id if self.stage_done else False})
            
    def test_04_action_done_and_cancel(self):
        """Test action_done and action_cancel methods on task"""
        approval = self.env['manager.approval'].create({
            'task': self.task.name,
            'project_id': self.project.id,
            'user_ids': self.task.user_ids.ids,
            'task_id': self.task.id
        })
        self.task.manager_approval_id = approval.id
        
        self.task.with_user(self.user_manager).action_done()
        self.assertEqual(self.task.stage_id.id, self.stage_done.id if self.stage_done else False)
        self.assertTrue(approval.button_view_boolean)
        
        self.task.with_user(self.user_manager).action_cancel()
        self.assertEqual(self.task.stage_id.id, self.stage_cancelled.id if self.stage_cancelled else False)
        self.assertTrue(approval.button_view_boolean_cancel)
