# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ruksana P (odoo@cybrosys.com)
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
from odoo import fields, models


class ProjectTask(models.Model):
    """
    ProjectTask model extends the project task model in the Odoo
    framework. It adds Create Expense button to create expense request and smart
    button Expense , to view all expenses related to that task.
    """
    _inherit = 'project.task'

    expense_count = fields.Integer(string='Expense Count',
                                   help='count of total expenses',
                                   compute='_compute_expense_count')

    def _compute_expense_count(self):
        """To calculate the count of expenses"""
        for rec in self:
            rec.expense_count = self.env['hr.expense'].search_count(
                [('task_id', '=', rec.id,)])

    def action_create_task_expense(self):
        """By clicking Create Expense Button which will go to Expense Request
        form where we can add the total amount of expense and also pass the
        value through context
        """
        return {
            'name': 'Create Expense Record',
            'type': 'ir.actions.act_window',
            'res_model': 'expense.request',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
                'default_project_id': self.project_id.id,
                'default_name': self.name,
                'default_employee_name_id': [
                    (6, 0, self.user_id.mapped('employee_ids').ids)]
            },
        }

    def action_view_expense(self):
        """ Smart Button Expense which will redirect to Current Expense
        Records"""
        expense_ids = self.env['hr.expense'].search(
            [('task_id', '=', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense',
            'domain': [('id', 'in', expense_ids)],
            'view_mode': 'tree,form',
            'target': 'current',
        }
