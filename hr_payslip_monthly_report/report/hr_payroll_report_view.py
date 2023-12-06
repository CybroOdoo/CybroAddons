# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models, tools
from datetime import date
import time
from calendar import monthrange


class PayrollReportView(models.Model):
    """Create a model 'hr.payroll.report.view' with details"""
    _name = 'hr.payroll.report.view'
    _description = "Hr Payroll Report view"
    _auto = False

    date = date.today()
    month = monthrange(date.year, date.month)
    start_date = fields.Date(string="Start Date",
                             default=time.strftime('%Y-%m-01'), invisible=True,
                             help="Mention the start date")
    end_date = fields.Date(string="End Date",
                           default=time.strftime('%Y-%m-01'), invisible=True,
                           help="Mention the end date")
    name = fields.Many2one('hr.employee', string='Employee',
                           help="Nane of the employee")
    date_from = fields.Date(string='From', help="Mention the from date")
    date_to = fields.Date(string='To', help="Mention the to date")
    state = fields.Selection([('draft', 'Draft'),
                              ('verify', 'Waiting'), ('done', 'Done'),
                              ('cancel', 'Rejected')],
                             string='Status', help="States regarding the report")
    job_id = fields.Many2one('hr.job', string='Job Title',
                             help="Job title of the person")
    company_id = fields.Many2one('res.company', string='Company',
                                 help="Company of the person")
    department_id = fields.Many2one('hr.department',
                                    string='Department',
                                    help="Company of the person")
    rule_name_id = fields.Many2one('hr.salary.rule.category',
                                   string="Rule Category",
                                   help="Mention the rule category")
    rule_amount = fields.Float(string="Amount", help="Mention the amount")
    struct_id = fields.Many2one('hr.payroll.structure',
                                string="Salary Structure",
                                help="Give the corresponding salary structure")
    rule_id = fields.Many2one('hr.salary.rule',
                              string="Salary Rule", help="Select the "
                                                         "salary rule")

    def _select(self):
        """ This function returns a SQL query string. This query string selects
         various columns from different database tables using SQL syntax."""
        select_str = """
            min(psl.id),ps.id,ps.number,emp.id as name,dp.id as department_id,
            jb.id as job_id,cmp.id as company_id,ps.date_from, ps.date_to,
             ps.state as state ,rl.id as rule_name_id, 
            psl.total as rule_amount,ps.struct_id as
             struct_id,rlu.id as rule_id"""
        return select_str

    def _from(self):
        """ This function returns a SQL query string. This query string selects
         various columns from different database tables and specifies the source
          tables and the necessary join conditions for a SQL query"""
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
        """This code defines a method named _group_by that returns a string
        representing a SQL GROUP BY clause. This clause is used in SQL queries
         to group the results by specific columns."""
        group_by_str = """group by ps.number,ps.id,emp.id,dp.id,jb.id,
        cmp.id,ps.date_from,ps.date_to,ps.state,
            psl.total,psl.name,psl.category_id,rl.id,rlu.id"""
        return group_by_str

    def init(self):
        """ This method appears to be related to database views and is used
         to create or replace a database view."""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as ( SELECT
                   %s
                   FROM %s
                   %s
                   )""" % (self._table, self._select(), self._from(),
                           self._group_by()))
