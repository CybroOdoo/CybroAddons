# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCreateExpenseFromTask(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Demo Employee',
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Demo User',
            'login': 'demo_user_expense',
            'email': 'demo@test.com',
            'employee_ids': [Command.link(cls.employee.id)],
        })
        cls.project = cls.env['project.project'].create({
            'name': 'Test Project',
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Test Task',
            'project_id': cls.project.id,
            'user_ids': [Command.link(cls.user.id)],
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Service Product',
            'type': 'service',
        })

    def test_action_create_task_expense(self):
        """Test expense wizard action."""
        action = self.task.action_create_task_expense()
        self.assertEqual(
            action['type'],
            'ir.actions.act_window'
        )
        self.assertEqual(
            action['res_model'],
            'expense.amount'
        )
        self.assertEqual(
            action['target'],
            'new'
        )
        self.assertEqual(
            action['context']['default_task_id'],
            self.task.id
        )

    def test_smart_expense(self):
        """Test smart expense action."""
        expense = self.env['hr.expense'].create({
            'employee_id': self.employee.id,
            'name': 'Task Expense',
            'project_id': self.project.id,
            'task_id': self.task.id,
            'product_id': self.product.id,
            'total_amount': 100,
        })
        action = self.task.smart_expense()
        self.assertEqual(
            action['type'],
            'ir.actions.act_window'
        )
        self.assertEqual(
            action['res_model'],
            'hr.expense'
        )
        self.assertIn(
            expense.id,
            action['domain'][0][2]
        )

    def test_action_create_expense(self):
        """Test expense creation from wizard."""
        wizard = self.env['expense.amount'].with_context({
            'default_name': self.task.name,
            'default_project_id': self.project.id,
        }).create({
            'product_id': self.product.id,
            'employee_name_ids': [Command.link(self.employee.id)],
            'total_amount': 500,
        })
        expense_ids = wizard.action_create_expense()
        self.assertTrue(expense_ids)
        expense = self.env['hr.expense'].browse(expense_ids[0])
        self.assertEqual(
            expense.employee_id,
            self.employee
        )
        self.assertEqual(
            expense.project_id,
            self.project
        )
        self.assertEqual(
            expense.total_amount,
            500
        )

    def test_expense_amount_split(self):
        """Test expense split between employees."""
        second_employee = self.env['hr.employee'].create({
            'name': 'Second Employee',
        })
        wizard = self.env['expense.amount'].with_context({
            'default_name': self.task.name,
            'default_project_id': self.project.id,
        }).create({
            'product_id': self.product.id,
            'employee_name_ids': [
                Command.link(self.employee.id),
                Command.link(second_employee.id),
            ],
            'total_amount': 1000,
        })
        expense_ids = wizard.action_create_expense()
        self.assertEqual(
            len(expense_ids),
            2
        )
        expenses = self.env['hr.expense'].browse(expense_ids)
        for expense in expenses:
            self.assertEqual(
                expense.total_amount,
                500
            )