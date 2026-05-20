# -*- coding: utf-8 -*-
#############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class DailyExpenseWizard(models.TransientModel):
    """
    Wizard for mass-creating daily expenses for employees assigned to a task,
    based on their recorded timesheet hours and hourly wage.
    """
    _name = 'daily.expense.wizard'
    _description = 'Daily Expense Wizard'

    task_id = fields.Many2one('project.task', string="Task", required=True,
                              help="Task for which daily expenses will be calculated.")
    date = fields.Date(string="Date", required=True,
                       default=fields.Date.context_today,
                       help="Date for which to compute expenses from timesheet entries.")
    product_id = fields.Many2one(
        'product.product',
        string="Expense Category",
        domain="[('is_oil_gas_expense_category', '=', True)]",
        required=True,
        help="Expense product category applied to the generated HR expense records."
    )
    task_employee_ids = fields.Many2many(
        'hr.employee',
        compute='_compute_task_employee_ids',
        string="Task Employees",
        help="All employees and assignees available on the selected task."
    )
    excluded_employee_ids = fields.Many2many(
        'hr.employee',
        string="Excluded Employees",
        domain="[('id', 'in', task_employee_ids)]",
        help="Employees to exclude from the daily expense calculation."
    )

    @api.depends('task_id', 'task_id.employee_ids', 'task_id.user_ids.employee_id')
    def _compute_task_employee_ids(self):
        for wizard in self:
            employees = self.env['hr.employee']
            if wizard.task_id:
                employees |= wizard.task_id.employee_ids
                employees |= wizard.task_id.user_ids.mapped('employee_id')
            wizard.task_employee_ids = employees

    def action_create_expense(self):
        """
        Calculates and creates 'task.daily.expense' records for all non-excluded
        employees assigned to the task for the selected date, linking them to an
        'hr.expense' record.
        """
        expense_env = self.env['task.daily.expense']
        hr_expense_env = self.env['hr.expense']
        for wizard in self:
            employees_to_process = wizard.task_employee_ids - wizard.excluded_employee_ids
            for employee in employees_to_process:
                timesheet_lines = self.env['account.analytic.line'].search([
                    ('employee_id', '=', employee.id),
                    ('task_id', '=', wizard.task_id.id),
                    ('date', '=', wizard.date)
                ])
                total_hours = sum(timesheet_lines.mapped('unit_amount'))
                amount = total_hours * employee.hourly_wage
                if amount <= 0:
                    continue

                # Check for existing draft oil and gas expense for this employee
                hr_expense = hr_expense_env.search([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'draft'),
                    ('task_id', '=', wizard.task_id.id),
                    ('is_oil_gas_expense', '=', True)
                ], limit=1)

                if not hr_expense:
                    hr_expense_vals = {
                        'name': 'Daily Expense - %s' % wizard.task_id.name,
                        'employee_id': employee.id,
                        'is_oil_gas_expense': True,
                        'project_id': wizard.task_id.project_id.id,
                        'task_id': wizard.task_id.id,
                        'product_id': wizard.product_id.id,
                    }
                    if wizard.task_id.project_id.account_id:
                        hr_expense_vals['analytic_distribution'] = {str(wizard.task_id.project_id.account_id.id): 100.0}

                    hr_expense = hr_expense_env.create(hr_expense_vals)

                existing_daily = expense_env.search([
                    ('employee_id', '=', employee.id),
                    ('task_id', '=', wizard.task_id.id),
                    ('date', '=', wizard.date),
                ], limit=1)

                if existing_daily:
                    # Update the expense amount
                    existing_daily.amount = amount
                    existing_daily.expense_id = hr_expense.id
                else:
                    # Create only if not exists
                    expense_env.create({
                        'employee_id': employee.id,
                        'task_id': wizard.task_id.id,
                        'date': wizard.date,
                        'amount': amount,
                        'expense_id': hr_expense.id,
                    })
