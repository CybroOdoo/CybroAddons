# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
from datetime import timedelta
from odoo import api, fields, models
from odoo.tools import date_utils


class HrLeaveReport(models.AbstractModel):
    """Model for the dashboard for viewing the employees leave"""
    _name = 'report.hr_leave_dashboard.hr_leave_report'
    _description = 'HR Leave Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Function for getting the report values"""
        today = fields.Date.today()
        if data.get('duration') == 'this_month':
            start_of_month = date_utils.start_of(today, 'month')
            end_of_month = date_utils.end_of(today, 'month') - timedelta(days=1)
            option = self.generate_date_range(start_of_month, end_of_month)
        elif data.get('duration') == 'this_year':
            start_of_year = date_utils.start_of(today, 'year')
            end_of_year = date_utils.end_of(today, 'year') - timedelta(days=1)
            option = self.generate_date_range(start_of_year, end_of_year)
        elif data.get('duration') == 'this_week':
            start_of_week = date_utils.start_of(today, 'week')
            end_of_week = date_utils.end_of(today, 'week')
            option = self.generate_date_range(start_of_week, end_of_week)
        else:
            option = [str(today)]

        if not self.env.user.employee_ids.child_ids:
            query = """SELECT l.id, lt.id as hr_leave_type_id, e.id as 
            emp_id, e.name as emp_name, e.department_id as emp_department, 
            e.parent_id as emp_parent_id, request_date_from, request_date_to, 
            l.number_of_days, lt.name ::jsonb->> 'en_US' as leave_type, 
            SUM(al.number_of_days) AS allocated_days, SUM(CASE WHEN l.state = 
            'validate' THEN l.number_of_days ELSE 0 END) AS taken_days, 
            SUM(al.number_of_days) - SUM(CASE WHEN l.state = 'validate' THEN 
            l.number_of_days ELSE 0 END) AS balance_days FROM hr_employee e 
            inner join hr_leave_allocation al ON al.employee_id = e.id inner 
            join hr_leave l on l.employee_id = e.id inner join hr_leave_type 
            lt on l.holiday_status_id = lt.id WHERE l.state = 'validate' AND 
            e.department_id = '%s' GROUP BY e.id,lt.id,l.id""" % \
                    self.env.user.employee_ids.department_id.id
        else:
            query = """SELECT l.id, lt.id as hr_leave_type_id, e.id as 
            emp_id, e.name as emp_name, e.department_id as emp_department, 
            e.parent_id as emp_parent_id, request_date_from, request_date_to, 
            l.number_of_days, lt.name ::jsonb->> 'en_US' as leave_type, 
            SUM(al.number_of_days) AS allocated_days, SUM(CASE WHEN l.state = 
            'validate' THEN l.number_of_days ELSE 0 END) AS taken_days, 
            SUM(al.number_of_days) - SUM(CASE WHEN l.state = 'validate' THEN 
            l.number_of_days ELSE 0 END) AS balance_days FROM hr_employee e 
            inner join hr_leave_allocation al ON al.employee_id = e.id inner 
            join hr_leave l on l.employee_id = e.id inner join hr_leave_type 
            lt on l.holiday_status_id = lt.id WHERE l.state = 'validate' 
            GROUP BY e.id,lt.id,l.id"""

        self.env.cr.execute(query)
        leave_data = self.env.cr.dictfetchall()
        filtered_list = []
        filtered_tuple = []
        for leave in leave_data:
            leave_list = self.generate_date_range(leave.get('request_date_from'),
                                                  leave.get('request_date_to') - timedelta(days=1))
            for date in leave_list:
                if date in option:
                    filtered_list.append(leave)
                    break
        for leave in filtered_list:
            if (leave.get('hr_leave_type_id'), leave.get('emp_id')) in filtered_tuple:
                filtered_list.remove(leave)
            else:
                filtered_tuple.append(
                    (leave.get('hr_leave_type_id'), leave.get('emp_id')))
        return {
            'duration': data.get('duration'),
            'filtered_list': filtered_list,
        }

    def generate_date_range(self, start_date, end_date):
        """Generate a list of dates within the given range"""
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)
        return date_list
