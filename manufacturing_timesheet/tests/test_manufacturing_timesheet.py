# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from datetime import timedelta
from odoo import fields
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestManufacturingTimesheet(common.TransactionCase):
    """Test suite for manufacturing_timesheet module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Assembly Product',
            'type': 'consu',
        })
        cls.workcenter = cls.env['mrp.workcenter'].create({
            'name': 'Assembly Station 1',
            'costs_hour': 25.0,
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Worker',
            'user_id': cls.env.user.id,
        })
        loss = cls.env['mrp.workcenter.productivity.loss'].search([], limit=1)
        if not loss:
            loss_type = cls.env['mrp.workcenter.productivity.loss.type'].create({
                'name': 'Test Productive',
            })
            loss = cls.env['mrp.workcenter.productivity.loss'].create({
                'name': 'Normal Operation',
                'loss_type': 'productive',
                'loss_type_id': loss_type.id,
            })
        cls.loss = loss

    def test_01_fields_definition(self):
        """Test is_manufacturing field presence and defaults."""
        project = self.env['project.project'].create({
            'name': 'Test Project',
            'is_manufacturing': True,
        })
        self.assertTrue(project.is_manufacturing)

        task = self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': project.id,
        })
        line = self.env['account.analytic.line'].create({
            'name': 'Test Line',
            'task_id': task.id,
            'is_manufacturing': True,
        })
        self.assertTrue(line.is_manufacturing)

    def test_02_workorder_button_finish_creates_timesheet(self):
        """Test workorder button_finish generates project, task, and timesheets."""
        mo = self.env['mrp.production'].create({
            'product_id': self.product.id,
            'product_qty': 2.0,
        })
        now = fields.Datetime.now()
        workorder = self.env['mrp.workorder'].create({
            'name': 'Assembly WO',
            'workcenter_id': self.workcenter.id,
            'production_id': mo.id,
            'product_id': self.product.id,
            'duration_expected': 90.0,
            'date_start': now,
        })

        # Add productivity log
        productivity_vals = {
            'workorder_id': workorder.id,
            'workcenter_id': self.workcenter.id,
            'loss_id': self.loss.id,
            'user_id': self.env.user.id,
            'date_start': now,
            'date_end': now + timedelta(minutes=60),
            'duration': 60.0,
        }
        if 'employee_id' in self.env['mrp.workcenter.productivity']._fields:
            productivity_vals['employee_id'] = self.employee.id
        self.env['mrp.workcenter.productivity'].create(productivity_vals)

        # Finish workorder
        workorder.button_finish()

        # Check project created
        project = self.env['project.project'].search([
            ('name', '=', f"MO: {mo.name}"),
        ], limit=1)
        self.assertTrue(project, "A project for the MO should have been created.")
        self.assertTrue(project.is_manufacturing, "The project should have is_manufacturing=True.")

        # Check task created
        task_name = (
            f"{workorder.name} in {workorder.workcenter_id.name} for "
            f"{workorder.product_id.display_name} on {workorder.date_start}"
        )
        task = self.env['project.task'].search([
            ('name', '=', task_name),
            ('project_id', '=', project.id),
        ], limit=1)
        self.assertTrue(task, "A task for the work order should have been created.")
        self.assertEqual(task.allocated_hours, workorder.duration_expected)

        # Check timesheet created
        timesheet = self.env['account.analytic.line'].search([
            ('task_id', '=', task.id),
        ], limit=1)
        self.assertTrue(timesheet, "Timesheet line should have been created.")
        self.assertTrue(timesheet.is_manufacturing, "Timesheet line should have is_manufacturing=True.")
        self.assertEqual(timesheet.employee_id, self.employee)
        self.assertEqual(timesheet.unit_amount, 1.0)

    def test_03_workorder_reuse_project_and_task(self):
        """Test existing project and task reuse on subsequent workorder."""
        mo = self.env['mrp.production'].create({
            'product_id': self.product.id,
            'product_qty': 1.0,
        })
        now = fields.Datetime.now()
        wo1 = self.env['mrp.workorder'].create({
            'name': 'Step 1',
            'workcenter_id': self.workcenter.id,
            'production_id': mo.id,
            'product_id': self.product.id,
            'date_start': now,
            'duration_expected': 30.0,
        })
        wo1.button_finish()

        project_count_before = self.env['project.project'].search_count([
            ('name', '=', f"MO: {mo.name}"),
        ])
        self.assertEqual(project_count_before, 1)

        wo2 = self.env['mrp.workorder'].create({
            'name': 'Step 2',
            'workcenter_id': self.workcenter.id,
            'production_id': mo.id,
            'product_id': self.product.id,
            'date_start': now,
            'duration_expected': 45.0,
        })
        wo2.button_finish()

        project_count_after = self.env['project.project'].search_count([
            ('name', '=', f"MO: {mo.name}"),
        ])
        self.assertEqual(project_count_after, 1, "Should reuse the existing project for the same MO.")

    def test_04_fallback_employee_and_date(self):
        """Test date_start and employee fallback paths in button_finish."""
        mo = self.env['mrp.production'].create({
            'product_id': self.product.id,
            'product_qty': 1.0,
        })
        wo = self.env['mrp.workorder'].create({
            'name': 'Step Fallback',
            'workcenter_id': self.workcenter.id,
            'production_id': mo.id,
            'product_id': self.product.id,
        })

        self.env['mrp.workcenter.productivity'].create({
            'workorder_id': wo.id,
            'workcenter_id': self.workcenter.id,
            'loss_id': self.loss.id,
            'duration': 30.0,
        })

        wo.button_finish()

        project = self.env['project.project'].search([
            ('name', '=', f"MO: {mo.name}"),
        ], limit=1)
        task = self.env['project.task'].search([
            ('project_id', '=', project.id),
        ], limit=1)
        timesheet = self.env['account.analytic.line'].search([
            ('task_id', '=', task.id),
        ], limit=1)
        self.assertTrue(timesheet)
        self.assertEqual(timesheet.unit_amount, 0.0)
        self.assertEqual(timesheet.date, fields.Date.context_today(self))

    def test_05_action_and_menu(self):
        """Test manufacturing timesheet window action and menu."""
        action = self.env.ref('manufacturing_timesheet.manufacturing_timesheet_action')
        self.assertEqual(action.res_model, 'account.analytic.line')
        self.assertIn("is_manufacturing", action.domain)
        menu = self.env.ref('manufacturing_timesheet.manufacturing_timesheet_all_menu_root')
        self.assertEqual(menu.action, action)
