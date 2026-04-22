# -*- coding: utf-8 -*-
#############################################################################
#
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


class HrExpense(models.Model):
    """
    Extends 'hr.expense' to support specialized expenses related to Oil & Gas
    industry operations, particularly for project task daily expenses.
    """
    _inherit = 'hr.expense'

    is_oil_gas_expense = fields.Boolean(
        string="Is Oil and Gas Expense",
        help="Mark this if the expense is specifically for oil and gas operations.")
    project_id = fields.Many2one(
        'project.project',
        string="Project",
        help="Select the project corresponding to this expense.")
    task_id = fields.Many2one(
        'project.task',
        string="Task",
        domain="[('project_id', '=', project_id)]",
        help="Select the task corresponding to this expense.")
    daily_expense_line_ids = fields.One2many(
        'task.daily.expense',
        'expense_id',
        string="Daily Expense Lines",
        help="Related daily expense lines generated for tasks.")

    @api.depends('is_oil_gas_expense', 'daily_expense_line_ids', 'daily_expense_line_ids.amount')
    def _compute_total_amount_currency(self):
        super()._compute_total_amount_currency()
        for rec in self:
            if rec.is_oil_gas_expense and rec.daily_expense_line_ids:
                rec.total_amount_currency = sum(rec.daily_expense_line_ids.mapped('amount'))
