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
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    """
    Inherits from 'account.analytic.line' (Timesheets) to enforce that only employees
    assigned to a task can record time against it.
    """
    _inherit = 'account.analytic.line'

    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        help="Select the employee."
    )

    @api.onchange('task_id')
    def _onchange_task_id_employee_domain(self):
        """
        Updates the domain for the employee field based on the selected task's
        assigned users. Also auto-sets the employee to the current user's employee.
        """
        if self.task_id:
            domain = ['|',
                      ('id', 'in', self.task_id.employee_ids.ids),
                      ('user_id', 'in', self.task_id.user_ids.ids)
                      ]

            # Auto-set logged-in employee
            user_employee = self.env.user.employee_id
            if user_employee and (user_employee.id in self.task_id.employee_ids.ids or user_employee.user_id in self.task_id.user_ids):
                self.employee_id = user_employee

            return {'domain': {'employee_id': domain}}
        else:
            return {'domain': {'employee_id': []}}

    @api.constrains('employee_id', 'task_id')
    def _check_employee_in_task(self):
        """
        Validates that the selected employee's user is indeed assigned to the task.
        """
        for rec in self:
            if rec.task_id and rec.employee_id:
                if rec.employee_id.user_id not in rec.task_id.user_ids and rec.employee_id.id not in rec.task_id.employee_ids.ids:
                    raise ValidationError(_(
                        "Selected employee is not assigned to this task.")
                    )
