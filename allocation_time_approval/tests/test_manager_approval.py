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

class TestManagerApproval(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestManagerApproval, cls).setUpClass()
        
        # Create user groups if not assigned
        group_manager = cls.env.ref('project.group_project_manager')
        group_employee = cls.env.ref('base.group_user')

        # Setup similar base data
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Manager User',
            'login': 'manager_user2',
            'email': 'manager@example.com',
            'groups_id': [(6, 0, [group_manager.id, group_employee.id])]
        })
        
        cls.stage_new = cls.env.ref("project.project_stage_0", raise_if_not_found=False)
        if not cls.stage_new:
            cls.stage_new = cls.env['project.task.type'].search([], order='sequence asc', limit=1)
        cls.stage_in_progress = cls.env.ref("project.project_stage_1", raise_if_not_found=False)
        cls.stage_cancelled = cls.env.ref("project.project_stage_3", raise_if_not_found=False)
        
        cls.project = cls.env['project.project'].create({
            'name': 'Test Project',
        })
        
        cls.task = cls.env['project.task'].create({
            'name': 'Approval Task',
            'project_id': cls.project.id,
            'stage_id': cls.stage_new.id if cls.stage_new else False
        })
        
        cls.approval = cls.env['manager.approval'].create({
            'task': 'Approval Task updated',
            'project_id': cls.project.id,
            'user_ids': [(4, cls.user_manager.id)],
            'planned_hours': 5.0,
            'task_id': cls.task.id
        })

    def test_01_action_approve(self):
        """Test manager approving the allocation"""
        self.approval.with_user(self.user_manager).action_approve()
        
        # Verify task is updated
        self.assertEqual(self.task.stage_id.id, self.stage_in_progress.id if self.stage_in_progress else False)
        self.assertEqual(self.task.allocated_hours, 5.0)
        self.assertEqual(self.task.name, 'Approval Task updated')
        
        # Verify buttons are toggled
        self.assertTrue(self.approval.button_view_boolean)
        self.assertFalse(self.approval.button_view_boolean_cancel)

    def test_02_action_manager_cancel(self):
        """Test manager cancelling the allocation"""
        self.approval.with_user(self.user_manager).action_manager_cancel()
        
        # Verify task is updated to cancelled
        self.assertEqual(self.task.stage_id.id, self.stage_cancelled.id if self.stage_cancelled else False)
        
        # Verify buttons are toggled
        self.assertFalse(self.approval.button_view_boolean)
        self.assertTrue(self.approval.button_view_boolean_cancel)
