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
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class TaskDailyExpense(models.Model):
    """
    Model for tracking daily expenses incurred by employees during specific project tasks.
    """
    _name = 'task.daily.expense'
    _description = 'Task Daily Expense'

    task_id = fields.Many2one('project.task',
                              string="Task",
                              help="Project task this daily expense is recorded against.")
    employee_id = fields.Many2one('hr.employee',
                                  string="Employee", required=True,
                                  help="Employee who incurred this daily expense."
                                  )
    project_id = fields.Many2one('project.project',
                                 related='task_id.project_id',
                                 help="Project derived from the linked task (auto-populated)."
                                 )
    date = fields.Date(string="Date", default=fields.Date.context_today,
                       help="Date when this expense was incurred.")
    amount = fields.Float(string="Expense Amount",
                          help="Total expense amount calculated from timesheet hours and hourly wage.")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help="Company responsible for this expense record."
    )
    expense_id = fields.Many2one('hr.expense',
                                 string="Expense",
                                 help="Link to the corresponding HR Expense record.")

    @api.constrains('amount')
    def _check_amount(self):
        """
        Ensures that the expense amount is not negative.
        """
        for rec in self:
            if rec.amount < 0:
                raise ValidationError(_("Expense amount cannot be negative."))

    @api.constrains('employee_id', 'task_id', 'date')
    def _check_duplicate_expense(self):
        """
        Ensures that an employee does not have multiple expenses on the same task for the same date.
        """
        for rec in self:
            if rec.employee_id and rec.task_id and rec.date:
                duplicate = self.search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('task_id', '=', rec.task_id.id),
                    ('date', '=', rec.date),
                    ('id', '!=', rec.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(_(
                        "An expense is already present for the employee %(employee)s "
                        "on task %(task)s for the date %(date)s."
                    ) % {
                        'employee': rec.employee_id.name,
                        'task': rec.task_id.name,
                        'date': rec.date,
                    })
