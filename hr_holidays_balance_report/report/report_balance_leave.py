# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
from odoo import fields, models, tools


class ReportBalanceLeave(models.Model):
    """Balance Leave Report model"""

    _name = 'report.balance.leave'
    _description = 'Leave Balance Report'
    _auto = False

    emp_id = fields.Many2one('hr.employee', string="Employee", readonly=True,
                             help="Employee name")
    gender = fields.Char(string='gender', readonly=True,
                         help="Employee Gender")
    department_id = fields.Many2one('hr.department', string='Department',
                                    readonly=True, help="Department Name")
    country_id = fields.Many2one('res.country', string='Nationality',
                                 readonly=True, help="Country Name")
    job_id = fields.Many2one('hr.job', string='Job', readonly=True,
                             help="Job of employee")
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type',
                                    readonly=True, help="Leave type of "
                                                        "employee")
    allocated_days = fields.Integer(string='Allocated Balance',
                                    help="Total leave assigned to "
                                         "the employee")
    taken_days = fields.Integer(string='Taken Leaves', help="Taken leaves of "
                                                            "employee")
    balance_days = fields.Integer(string='Remaining Balance',
                                  help="Remaining leaves of employee")
    company_id = fields.Many2one('res.company', string="Company",
                                 help="Company Name")

    def init(self):
        """Loads report data"""
        tools.drop_view_if_exists(self._cr, 'report_balance_leave')
        self._cr.execute("""
            CREATE or REPLACE view report_balance_leave as (
            SELECT row_number() over(ORDER BY e.id) as id,
                e.id AS emp_id,
                e.gender as gender,
                e.country_id as country_id,
                e.department_id as department_id,
                e.job_id as job_id,
                lt.id AS leave_type_id,SUM(al.number_of_days) AS allocated_days
                ,SUM(CASE WHEN l.state ='validate' THEN l.number_of_days ELSE 0
                END) AS taken_days,SUM(al.number_of_days) - SUM(CASE WHEN 
                l.state = 'validate' THEN l.number_of_days ELSE 0 END) AS 
                balance_days, e.company_id as company_id
            FROM
                hr_employee e
                JOIN hr_leave_allocation al ON al.employee_id = e.id
                JOIN hr_leave_type lt ON al.holiday_status_id = lt.id
                LEFT JOIN hr_leave l ON l.employee_id = e.id AND 
                l.holiday_status_id = lt.id
            WHERE
                e.active = True
            GROUP BY
                e.id,
                lt.id)
            """)
