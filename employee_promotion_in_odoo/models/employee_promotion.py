# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
from odoo import api, fields, models
from odoo.exceptions import UserError


class EmployeePromotion(models.Model):
    """This model is necessary for add employee promotion details in employee
       module """
    _name = 'employee.promotion'
    _description = 'Employee Promotion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'promotion_name'

    promotion_name = fields.Text(required=True, string='Promotion Name',
                                 help='Promotion name')
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, help='Name of employee')
    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  help='Contract of employee',
                                  domain="[('employee_id', '=', employee_id)]")
    job_title_id = fields.Many2one('hr.job', string='Old Designation',
                                   help='Previous job of employee ')
    job_salary = fields.Float(string='Previous Salary',
                              required=True, help='Previous job salary')
    promotion_date = fields.Date(string='Promotion Date',
                                 default=fields.Date.today(),
                                 help='Date of promotion date')
    promotion_type_id = fields.Many2one('promotion.type',
                                        string='Promotion Type',
                                        required=True,
                                        help='Promotion type of promotion')
    new_designation_id = fields.Many2one('hr.job', string='New Designation',
                                         required=True,
                                         help='New designation of employee')
    new_salary = fields.Float(string='New Salary', required=True,
                              help='New salary')
    description = fields.Text(string='Description', help='Description')

    @api.model
    def create(self, vals):
        """It checks if the new salary is greater than the old salary,
           raising a UserError if it is not the case."""
        res = super(EmployeePromotion, self).create(vals)
        employee = self.env['hr.employee'].browse(res.employee_id.id)
        employee.write({
            'promotion_ids': [(4, res.id)],
            'job_id': res.new_designation_id.id
        })
        if res.job_salary >= res.new_salary:
            raise UserError("New Salary will be Higher than Old ")
        return res

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """This method is called when the employee_id field is changed.
           It searches for an open HR contract history
           record for the selected employee and sets the contract_id and
           job_salary fields based on the
           corresponding values in the contract.
           If no open contract is found, the fields are left blank."""
        self.job_title_id = self.employee_id.job_id.id
        contract = self.env['hr.contract.history'].search(
            [('employee_id', '=', self.employee_id.id),
             ('state', '=', 'open')])
        if contract:
            for contract_history in contract:
                self.contract_id = contract_history.name
                self.job_salary = contract_history.wage

    def write(self, vals):
        """ Override the default write method to check if the new salary is
            greater than the current job salary.
            If the new salary is greater,
            raise a UserError with a warning message."""
        res = super(EmployeePromotion, self).write(vals)
        if self.job_salary >= self.new_salary:
            raise UserError("New Salary will be Higher than Old ")
        return res
