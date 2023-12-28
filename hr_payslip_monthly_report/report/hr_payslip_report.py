# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import time
from calendar import monthrange
from datetime import date

from odoo import fields, models, tools


class HrPayrollReportView(models.Model):
    """Create a new model for getting monthly report"""
    _name = 'hr.payroll.report'
    _auto = False

    now = date.today()
    month_day = monthrange(now.year, now.month)
    start_date = fields.Date(string="Start Date",
                             default=time.strftime('%Y-%m-01'), invisible=True,
                             help="Start Date for Report")
    end_date = fields.Date(string="End Date", default=time.strftime(
        '%Y-%m-' + str(month_day[1]) + ''), invisible=True,
                           help="End Date for Report")
    name = fields.Many2one('hr.employee', string='Employee',
                           help="Choose Employee")
    date_from = fields.Date(string='From', help="Starting Date for Report")
    date_to = fields.Date(string='To', help="Ending Date for Report")
    state = fields.Selection(
        [('draft', 'Draft'), ('verify', 'Waiting'), ('done', 'Done'),
         ('cancel', 'Rejected')],
        string='Status', help="Select Status for Report")
    job_id = fields.Many2one('hr.job', string='Job Title',
                             help="Choose Hr Job")
    company_id = fields.Many2one('res.company', string='Company',
                                 help="Choose Company")
    department_id = fields.Many2one('hr.department',
                                    string='Department',
                                    help="Choose Hr Department")
    rule_name = fields.Many2one('hr.salary.rule.category',
                                string="Rule Category",
                                help="Choose Salary Rule Category")
    rule_amount = fields.Float(string="Amount", help="Set Amount")
    struct_id = fields.Many2one('hr.payroll.structure',
                                string="Salary Structure",
                                help="Choose Hr Payroll Structure")
    rule_id = fields.Many2one('hr.salary.rule',
                              string="Salary Rule", help="Choose Salary Rule")

    def _select(self):
        """
            Generate and return a SQL SELECT statement for retrieving specific fields from the database.
            Returns:
                str: SQL SELECT statement with the following fields:
                    - Minimum of psl.id
                    - ps.id
                    - ps.number
                    - emp.id as name
                    - dp.id as department_id
                    - jb.id as job_id
                    - cmp.id as company_id
                    - ps.date_from
                    - ps.date_to
                    - ps.state as state
                    - rl.id as rule_name
                    - psl.total as rule_amount
                    - ps.struct_id as struct_id
                    - rlu.id as rule_id
            """
        select_str = """
            min(psl.id),ps.id,ps.number,emp.id as name,dp.id as 
            department_id,jb.id as job_id,cmp.id as company_id,ps.date_from, 
            ps.date_to, ps.state as state ,rl.id as rule_name, 
            psl.total as rule_amount,ps.struct_id as struct_id,rlu.id as rule_id
            """
        return select_str

    def _from(self):
        """
            Generate and return a SQL FROM clause for joining tables in a
            database query.

            Returns:
                str: SQL FROM clause with the following table joins:
                    - hr_payslip_line (psl)
                    - hr_payslip (ps) on ps.id = psl.slip_id
                    - hr_salary_rule (rlu) on rlu.id = psl.salary_rule_id
                    - hr_employee (emp) on ps.employee_id = emp.id
                    - hr_salary_rule_category (rl) on rl.id = psl.category_id
                    - hr_department (dp) (left join) on emp.department_id = dp.id
                    - hr_job (jb) (left join) on emp.job_id = jb.id
                    - res_company (cmp) on cmp.id = ps.company_id
            """
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
        """
            Generate and return a SQL GROUP BY clause for grouping results in a
            database query.

            Returns:
                str: SQL GROUP BY clause with the following fields:
                    - ps.number
                    - ps.id
                    - emp.id
                    - dp.id
                    - jb.id
                    - cmp.id
                    - ps.date_from
                    - ps.date_to
                    - ps.state
                    - psl.total
                    - psl.name
                    - psl.category_id
                    - rl.id
                    - rlu.id
            """
        group_by_str = """group by ps.number,ps.id,emp.id,dp.id,jb.id,cmp.id,
        ps.date_from,ps.date_to,ps.state,
            psl.total,psl.name,psl.category_id,rl.id,rlu.id"""
        return group_by_str

    def init(self):
        """
            Initialize or update a database view with a SELECT statement.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as ( SELECT
                   %s
                   FROM %s
                   %s
                   )""" % (
            self._table, self._select(), self._from(), self._group_by()))
