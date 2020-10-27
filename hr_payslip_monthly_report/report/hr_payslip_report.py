# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Anusha (<https://www.cybrosys.com>)
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

from odoo import fields, models, tools
from datetime import date
import time
from calendar import monthrange


class PayrollReportView(models.Model):
    _name = 'hr.payroll.report.view'
    _auto = False

    now = date.today()
    month_day = monthrange(now.year, now.month)
    start_date = fields.Date(string="Start Date", default=time.strftime('%Y-%m-01'), invisible=True)
    end_date = fields.Date(string="End Date", default=time.strftime('%Y-%m-' + str(month_day[1]) + ''), invisible=True)
    name = fields.Many2one('hr.employee', string='Employee')
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    state = fields.Selection([('draft', 'Draft'), ('verify', 'Waiting'), ('done', 'Done'), ('cancel', 'Rejected')],
                             string='Status')
    job_id = fields.Many2one('hr.job', string='Job Title')
    company_id = fields.Many2one('res.company', string='Company')
    department_id = fields.Many2one('hr.department', string='Department')
    rule_name = fields.Many2one('hr.salary.rule.category', string="Rule Category")
    rule_amount = fields.Float(string="Amount")
    struct_id = fields.Many2one('hr.payroll.structure', string="Salary Structure")
    rule_id = fields.Many2one('hr.salary.rule', string="Salary Rule")

    def _select(self):
        select_str = """
            min(psl.id),ps.id,ps.number,emp.id as name,dp.id as department_id,jb.id as job_id,cmp.id as company_id,ps.date_from, ps.date_to, ps.state as state ,rl.id as rule_name, 
            psl.total as rule_amount,ps.struct_id as struct_id,rlu.id as rule_id"""
        return select_str

    def _from(self):
        from_str = """
                hr_payslip_line psl   
                join hr_payslip ps on ps.id=psl.slip_id
                join hr_salary_rule rlu on rlu.id = psl.salary_rule_id
                join hr_employee emp on ps.employee_id=emp.id
                join hr_salary_rule_category rl on rl.id = psl.category_id
                left join hr_department dp on emp.department_id=dp.id
                left join hr_job jb on emp.job_id=jb.id
                join res_company cmp on cmp.id=ps.company_id
             """
        return from_str

    def _group_by(self):
        group_by_str = """group by ps.number,ps.id,emp.id,dp.id,jb.id,cmp.id,ps.date_from,ps.date_to,ps.state,
            psl.total,psl.name,psl.category_id,rl.id,rlu.id"""
        return group_by_str

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as ( SELECT
                   %s
                   FROM %s
                   %s
                   )""" % (self._table, self._select(), self._from(), self._group_by()))


