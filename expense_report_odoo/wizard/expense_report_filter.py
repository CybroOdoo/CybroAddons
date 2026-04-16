# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Afra (odoo@cybrosys.info)
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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ExpenseReportFilter(models.TransientModel):
    _name = 'expense.report.filter'
    _description = 'Expense Report Wizard'

    from_date = fields.Date(string='Start Date',
                            help="The start date for the expense period")
    to_date = fields.Date(string='End Date',
                          help="The end date for the expense period")
    employee_name_ids = fields.Many2many('hr.employee',
                                         string="Employee Name",
                                         default=lambda self: [
                                             (4, self.env.user.employee_id.id)],
                                         help="The employees associated with "
                                              "the expenses")
    state = fields.Selection([
        ('draft', 'To Report'),
        ('reported', 'To Submit'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('refused', 'Refused')
    ], string='Status', copy=False, index=True, default='draft',
        help="The current status of the expense report")

    @api.model_create_multi
    def create(self, vals):
        """This method ensures that an employee_name_ids field is
        set when creating an ExpenseWizard record, unless the
        current user has the 'base.group_system' security group."""
        if not vals[0]['employee_name_ids'] and not self.env.user.has_group(
                'base.group_system'):
            vals[0]['employee_name_ids'] = [(4, self.env.user.employee_id.id)]
        return super().create(vals)

    def action_expense_report(self):
        """Generate expense report based on filters"""
        query = """
            SELECT 
                hr_expense.date,
                hr_expense.product_id,
                hr_expense.name,
                hr_expense.employee_id,
                hr_expense.price_unit,
                hr_expense.quantity,
                hr_expense.currency_id,
                hr_expense.total_amount,
                hr_expense.state,
                pl.name AS t2,
                ep.name AS t3,
                currency.symbol AS t4
            FROM hr_expense
            LEFT JOIN product_product pd ON pd.id = hr_expense.product_id
            LEFT JOIN product_template pl ON pl.id = pd.product_tmpl_id
            LEFT JOIN hr_employee ep ON ep.id = hr_expense.employee_id
            LEFT JOIN res_currency currency ON currency.id = hr_expense.currency_id
            WHERE 1=1
        """
        params = []
        # Date filters
        if self.from_date:
            query += " AND hr_expense.date >= %s"
            params.append(self.from_date)

        if self.to_date:
            if self.from_date and self.to_date < self.from_date:
                raise ValidationError(_("End date cannot be before start date"))
            query += " AND hr_expense.date <= %s"
            params.append(self.to_date)

        # Employee filter
        if self.employee_name_ids:
            employee_ids = tuple(self.employee_name_ids.ids)
            query += " AND hr_expense.employee_id IN %s"
            params.append(employee_ids)
            emp_name = self.employee_name_ids.mapped('name')

        else:
            expenses = self.env['hr.expense'].search([
                ('state', '=', self.state)
            ]) if self.state else self.env['hr.expense'].search([])

            all_employees = expenses.mapped('employee_id')

            if all_employees:
                query += " AND hr_expense.employee_id IN %s"
                params.append(tuple(all_employees.ids))
            else:
                # Prevent SQL error when empty
                query += " AND 1=0"

            emp_name = all_employees.mapped('name')
        # State filter
        if self.state:
            query += " AND hr_expense.state = %s"
            params.append(self.state)

        # Execute query
        self.env.cr.execute(query, params)
        data = {
            'model_id': self.id,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'emp_name': emp_name,
            'state': self.state,
            'data_pdf': self.env.cr.dictfetchall()
        }
        return self.env.ref(
            'expense_report_odoo.action_expense_request_report'
        ).report_action(None, data=data)
