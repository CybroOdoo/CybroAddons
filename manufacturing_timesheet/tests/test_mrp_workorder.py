# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
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
################################################################################
from datetime import datetime
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestMrpWorkorder(TransactionCase):
    """Test cases for MrpWorkorder inheritance in manufacturing_timesheet."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Manufacturing Product',
            'type': 'consu',
        })

        # Create a workcenter
        cls.workcenter = cls.env['mrp.workcenter'].create({
            'name': 'Assembly Workcenter',
            'time_start': 0.0,
            'time_stop': 0.0,
            'costs_hour': 15.0,
        })

        # Create a manufacturing order (MO)
        cls.production = cls.env['mrp.production'].create({
            'product_id': cls.product.id,
            'product_qty': 1.0,
            'product_uom_id': cls.product.uom_id.id,
        })

        # Create a workorder
        cls.workorder = cls.env['mrp.workorder'].create({
            'name': 'Assemble Table',
            'production_id': cls.production.id,
            'workcenter_id': cls.workcenter.id,
            'date_start': datetime(2026, 6, 8, 10, 0, 0),
            'date_finished': datetime(2026, 6, 8, 12, 0, 0),
            'duration_expected': 120.0,
        })

        # Create an employee
        cls.employee = cls.env['hr.employee'].create({
            'name': 'John Doe',
        })

        # Find or create a productivity loss record
        cls.loss = cls.env['mrp.workcenter.productivity.loss'].search(
            [('loss_type', '=', 'productive')], limit=1
        )
        if not cls.loss:
            cls.loss = cls.env['mrp.workcenter.productivity.loss'].create({
                'name': 'Productive Time',
                'loss_type': 'productive',
                'sequence': 1,
            })

        # Create a productivity / time tracking entry linked to the workorder
        cls.productivity = cls.env['mrp.workcenter.productivity'].create({
            'workorder_id': cls.workorder.id,
            'workcenter_id': cls.workcenter.id,
            'loss_id': cls.loss.id,
            'date_start': datetime(2026, 6, 8, 10, 0, 0),
            'date_end': datetime(2026, 6, 8, 11, 0, 0),
            'duration': 60.0,
            'employee_id': cls.employee.id,
        })

    def test_workorder_finish_creates_project_task_and_timesheet(self):
        """Test that finishing a workorder creates a project, task and analytic line."""
        # Ensure no project or task exists for this MO before finishing
        existing_project = self.env['project.project'].search([
            ('name', '=', f"MO: {self.production.name}")
        ])
        self.assertFalse(existing_project, "Project should not exist yet.")

        # Finish the workorder
        self.workorder.button_finish()

        # Check that the project was created with is_manufacturing=True
        project = self.env['project.project'].search([
            ('name', '=', f"MO: {self.production.name}")
        ])
        self.assertTrue(project, "Project was not created.")
        self.assertTrue(project.is_manufacturing, "Project's is_manufacturing should be True.")

        # Check that the task was created under the project
        task_name = f"{self.workorder.name} in {self.workorder.workcenter_id.name} for " \
                    f"{self.workorder.product_id.display_name} on {self.workorder.date_start}"
        task = self.env['project.task'].search([
            ('name', '=', task_name),
            ('project_id', '=', project.id)
        ])
        self.assertTrue(task, "Task was not created.")
        self.assertEqual(task.date_assign, self.workorder.date_start)
        self.assertEqual(task.date_deadline, self.workorder.date_finished)
        self.assertEqual(task.allocated_hours, self.workorder.duration_expected)

        # Check that the timesheet (analytic line) was created
        timesheet = self.env['account.analytic.line'].search([
            ('task_id', '=', task.id),
            ('is_manufacturing', '=', True)
        ])
        self.assertTrue(timesheet, "Timesheet line was not created.")
        self.assertEqual(timesheet.date, self.productivity.date_start.date())
        self.assertEqual(timesheet.employee_id, self.employee)
        self.assertEqual(timesheet.unit_amount, self.productivity.duration / 60)
        self.assertEqual(
            timesheet.name,
            f"{self.workorder.name} in {self.workorder.workcenter_id.name} for {self.workorder.product_id.display_name}"
        )

    def test_workorder_finish_reuses_existing_project(self):
        """Test that if a project already exists for the MO, it is reused."""
        # Pre-create the project
        project = self.env['project.project'].create({
            'name': f"MO: {self.production.name}",
            'is_manufacturing': True,
        })

        # Finish the workorder
        self.workorder.button_finish()

        # Check that no duplicate project was created
        projects = self.env['project.project'].search([
            ('name', '=', f"MO: {self.production.name}")
        ])
        self.assertEqual(len(projects), 1, "There should be exactly one project.")
        self.assertEqual(projects[0], project, "The existing project should have been reused.")

    def test_workorder_finish_reuses_existing_task(self):
        """Test that if a task already exists for the workorder, it is reused."""
        # Pre-create the project
        project = self.env['project.project'].create({
            'name': f"MO: {self.production.name}",
            'is_manufacturing': True,
        })

        # Pre-create the task
        task_name = f"{self.workorder.name} in {self.workorder.workcenter_id.name} for " \
                    f"{self.workorder.product_id.display_name} on {self.workorder.date_start}"
        task = self.env['project.task'].create({
            'name': task_name,
            'project_id': project.id,
        })

        # Finish the workorder
        self.workorder.button_finish()

        # Check that no duplicate task was created
        tasks = self.env['project.task'].search([
            ('name', '=', task_name),
            ('project_id', '=', project.id)
        ])
        self.assertEqual(len(tasks), 1, "There should be exactly one task.")
        self.assertEqual(tasks[0], task, "The existing task should have been reused.")
