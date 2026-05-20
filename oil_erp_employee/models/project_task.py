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

from odoo import fields, models
from odoo.tools.translate import _


class ProjectTask(models.Model):
    """
    Extends 'project.task' to support employee assignment and daily expense tracking
    for oil field operations.
    """
    _inherit = 'project.task'

    employee_ids = fields.Many2many('hr.employee',
                                    string='Employees',
                                    help="Employees assigned to work on this task."
                                    )
    expense_count = fields.Integer(string='Expense Count',
                                   compute='_compute_expense_count',
                                   help="Total number of oil and gas daily expenses recorded for this task."
                                   )

    def _compute_expense_count(self):
        """ Count the oil and gas related HR expenses linked to this task."""
        for rec in self:
            rec.expense_count = self.env['hr.expense'].search_count([
                ('task_id', '=', rec.id),
                ('is_oil_gas_expense', '=', True)
            ])

    def action_calculate_daily_expense(self):
        """ Open the daily expense wizard to record employee expenses for this task. """
        self.ensure_one()
        return {
            'name': 'Daily Expense',
            'type': 'ir.actions.act_window',
            'res_model': 'daily.expense.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
            }
        }

    def action_view_expenses(self):
        """ Open the list of oil and gas HR expenses linked to this task. """
        self.ensure_one()
        action = {
            'name': _('HR Expenses'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense',
            'view_mode': 'list,form',
            'domain': [('task_id', '=', self.id), ('is_oil_gas_expense', '=', True)],
            'context': {
                'default_task_id': self.id,
                'default_is_oil_gas_expense': True,
                'search_default_draft': 1
            },
        }
        # Open form view directly when only one expense exists
        expense_ids = self.env['hr.expense'].search([('task_id', '=', self.id), ('is_oil_gas_expense', '=', True)])
        if len(expense_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = expense_ids.id
        return action
