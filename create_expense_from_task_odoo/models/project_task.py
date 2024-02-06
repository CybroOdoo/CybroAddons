# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import models


class InheritProjectTask(models.Model):
    """
    InheritProjectTask model extends the project.task model in the Odoo
    framework. It adds two methods - create_task_expense() and smart_expense()
    - which are used as button actions to create expense records associated
    with a task and display existing expense records related to a task,
    respectively.
    """
    _inherit = 'project.task'

    def action_create_task_expense(self):
        """Expense Button which will go to Expense Wizard Form where he add
        the total amount of expense and also pass the value through context"""
        return {
            'name': 'Create Expense Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'expense.amount',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
                'default_project_id': self.project_id.id,
                'default_name': self.name,
                'default_employee_name_id': [
                    (6, 0, self.user_ids.mapped('employee_ids').ids)]
            },
        }

    def smart_expense(self):
        """ Smart Button of Expense which will redirect to Current Expense
        Records"""
        expense_ids = self.env['hr.expense'].search([('task_id', '=', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense',
            'domain': [('id', 'in', expense_ids)],
            'view_mode': 'tree,form',
            'target': 'current',
        }
