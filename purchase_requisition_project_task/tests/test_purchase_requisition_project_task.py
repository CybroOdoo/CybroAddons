# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: K Sai Saran Varma(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestPurchaseRequisitionProjectTask(TransactionCase):
    """Test Cases for Purchase Requisition & Project Task Integration"""

    @classmethod
    def setUpClass(cls):
        super(TestPurchaseRequisitionProjectTask, cls).setUpClass()

        # Create Project
        cls.project = cls.env['project.project'].create({
            'name': 'Test Project'
        })

        # Create Tasks for the Project
        cls.task_1 = cls.env['project.task'].create({
            'name': 'Test Task 1',
            'project_id': cls.project.id
        })
        cls.task_2 = cls.env['project.task'].create({
            'name': 'Test Task 2',
            'project_id': cls.project.id
        })

        # Create Purchase Requisition
        cls.requisition = cls.env['purchase.requisition'].create({
            'project_id': cls.project.id,
            'task_ids': [(6, 0, [cls.task_1.id, cls.task_2.id])]
        })

    def test_01_onchange_project_task(self):
        """Test onchange project to auto-fill tasks in purchase requisition."""
        requisition = self.env['purchase.requisition'].new({
            'project_id': self.project.id
        })
        requisition._onchange_project_task()
        self.assertEqual(
            len(requisition.task_ids), 2,
            "Tasks should be auto-filled based on the project."
        )
        self.assertIn(
            self.task_1, requisition.task_ids,
            "Task 1 should be in the auto-filled tasks."
        )
        self.assertIn(
            self.task_2, requisition.task_ids,
            "Task 2 should be in the auto-filled tasks."
        )

    def test_02_project_purchase_count_and_action(self):
        """Test purchase_count and action_purchase_requisition in project.project."""
        # Test count
        self.project._compute_purchase_count()
        self.assertEqual(
            self.project.purchase_count, 1,
            "Project purchase count should be 1."
        )

        # Test action when requisition exists
        action = self.project.action_purchase_requisition()
        self.assertEqual(
            action.get('res_model'), 'purchase.requisition',
            "Action should open purchase.requisition model."
        )
        self.assertEqual(
            action.get('domain'), [('project_id', '=', self.project.id)],
            "Action domain should match the project."
        )

        # Create another project with no requisitions
        project2 = self.env['project.project'].create({'name': 'Project 2'})
        action2 = project2.action_purchase_requisition()
        self.assertEqual(
            action2.get('res_model'), 'purchase.requisition',
            "Action should open purchase.requisition model."
        )
        self.assertEqual(
            action2.get('context', {}).get('default_project_id'), project2.id,
            "Action context should set default project id."
        )
        self.assertTrue(
            action2.get('context', {}).get('default_is_project'),
            "Action context should set default_is_project to True."
        )

    def test_03_task_purchase_count_and_action(self):
        """Test purchase_count and action_purchase_requisition in project.task."""
        # Test count
        self.task_1._compute_purchase_count()
        self.assertEqual(
            self.task_1.purchase_count, 1,
            "Task purchase count should be 1."
        )

        # Test action when requisition exists
        action = self.task_1.action_purchase_requisition()
        self.assertEqual(
            action.get('res_model'), 'purchase.requisition',
            "Action should open purchase.requisition model."
        )
        self.assertEqual(
            action.get('domain'), [('task_ids', '=', self.task_1.id)],
            "Action domain should match the task."
        )

        # Test task with no requisition raises ValidationError
        task3 = self.env['project.task'].create({
            'name': 'Task 3',
            'project_id': self.project.id
        })
        with self.assertRaises(ValidationError):
            task3.action_purchase_requisition()
