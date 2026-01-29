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


class ExpenseRequest(models.TransientModel):
    """
    This wizard is used for creating expense records.It allows users to
    specify the service, the employee associated with the record, and the total
    amount for the record.
    """
    _name = 'expense.request'
    _description = "Project Task Expense Request"

    product_id = fields.Many2one('product.product', string="Service",
                                 domain=[('type', '=', 'service')],
                                 help="The product associated with the record")
    employee_ids = fields.Many2many('hr.employee', string="Employee",
                                    help="The employees associated with this "
                                         "record")
    total_amount = fields.Float(string="Total Amount",
                                help="The total amount for this record.")

    def action_create_expense(self):
        """Expense Creation if they are many assigned the amount is split
        between them"""
        expenses = [self.env['hr.expense'].create({
            'employee_id': employee.id,
            'date': fields.Date.today(),
            'name': self._context.get('default_name'),
            'project_id': self._context.get('default_project_id'),
            'total_amount': self.total_amount / len(self.employee_ids),
            'product_id': self.product_id.id,
            'unit_amount': self.product_id.standard_price
        }).id for employee in self.employee_ids]
        return expenses
