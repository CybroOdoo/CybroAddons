# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Treesa Maria Jude (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

import time
from datetime import datetime
from dateutil import relativedelta
from odoo import models, fields, api, _


class EmployeeInsurance(models.Model):
    _name = 'hr.insurance'
    _description = 'HR Insurance'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    policy_id = fields.Many2one('insurance.policy', string='Policy', required=True)
    amount = fields.Float(string='Policy Amount', required=True)
    sum_insured = fields.Float(string="Sum Insured", required=True)
    policy_coverage = fields.Selection([('monthly', 'Monthly'), ('yearly', 'Yearly')],
                                       required=True, default='monthly',
                                       string='Policy Coverage',)
    date_from = fields.Date(string='Date From',
                            default=time.strftime('%Y-%m-%d'), readonly=True)
    date_to = fields.Date(string='Date To',   readonly=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    state = fields.Selection([('active', 'Active'),
                              ('expired', 'Expired'), ],
                             default='active', string="State",compute='get_status')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)

    def get_status(self):
        current_datetime = datetime.now()
        for i in self:
            x = datetime.strptime(i.date_from, '%Y-%m-%d')
            y = datetime.strptime(i.date_to, '%Y-%m-%d')
            if x <= current_datetime and y >= current_datetime:
                i.state = 'active'

            else:
                i.state = 'expired'

    @api.constrains('policy_coverage')
    @api.onchange('policy_coverage')
    def get_policy_period(self):

        if self.policy_coverage == 'monthly':
            self.date_to = str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10]
        if self.policy_coverage == 'yearly':
            self.date_to = str(datetime.now() + relativedelta.relativedelta(months=+12))[:10]


class HrInsurance(models.Model):
    _inherit = 'hr.employee'

    insurance_percentage = fields.Float(string="Company Percentage ")
    deduced_amount_per_month = fields.Float(string="Salary deduced per month", compute="get_deduced_amount")
    deduced_amount_per_year = fields.Float(string="Salary deduced per year", compute="get_deduced_amount")
    insurance = fields.One2many('hr.insurance', 'employee_id', string="Insurance",
                                domain=[('state', '=', 'active')])

    def get_deduced_amount(self):
        current_datetime = datetime.now()
        for emp in self:
            ins_amount = 0
            for ins in emp.insurance:

                x = datetime.strptime(ins.date_from, '%Y-%m-%d')
                y = datetime.strptime(ins.date_to, '%Y-%m-%d')
                if x < current_datetime and y > current_datetime:
                    if ins.policy_coverage == 'monthly':

                        ins_amount = ins_amount + (ins.amount*12)
                    else:

                        ins_amount = ins_amount + ins.amount

            emp.deduced_amount_per_year = ins_amount-((ins_amount*emp.insurance_percentage)/100)
            emp.deduced_amount_per_month = emp.deduced_amount_per_year/12


class InsuranceRuleInput(models.Model):
    _inherit = 'hr.payslip'

    # insurance_amount = fields.Float("Insurance amount", compute='get_inputs')

    def get_inputs(self, contract_ids, date_from, date_to):
        """This Compute the other inputs to employee payslip.
                           """
        res = super(InsuranceRuleInput, self).get_inputs(contract_ids, date_from, date_to)

        contract_obj = self.env['hr.contract']
        for i in contract_ids:
            if contract_ids[0]:
                emp_id = contract_obj.browse(i[0].id).employee_id
                for result in res:
                    if emp_id.deduced_amount_per_month != 0 and result.get('code') == 'INSUR':
                                   result['amount'] = emp_id.deduced_amount_per_month
        return res

