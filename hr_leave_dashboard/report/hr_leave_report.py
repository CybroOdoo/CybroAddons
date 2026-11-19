# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#############################################################################
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
        data = data or {}
        today = fields.Date.context_today(self)
        duration = data.get('duration', 'today')
        if duration == 'this_month':
            start_of_month = date_utils.start_of(today, 'month')
            end_of_month = date_utils.end_of(today, 'month')
            option = self.generate_date_range(start_of_month, end_of_month)
        elif duration == 'this_year':
            start_of_year = date_utils.start_of(today, 'year')
            end_of_year = date_utils.end_of(today, 'year')
            option = self.generate_date_range(start_of_year, end_of_year)
        elif duration == 'this_week':
            start_of_week = date_utils.start_of(today, 'week')
            end_of_week = date_utils.end_of(today, 'week')
            option = self.generate_date_range(start_of_week, end_of_week)
        else:
            option = [str(today)]

        current_emp = self.env.user.employee_id
        lang = self.env.user.lang or 'en_US'
        dept_condition = ""
        params = [lang]

        if current_emp and not current_emp.child_ids and current_emp.department_id:
            dept_condition = "AND v.department_id = %s"
            params.append(current_emp.department_id.id)

        query = f"""
            SELECT l.id, wet.id as hr_leave_type_id, e.id as emp_id,
                   e.name as emp_name, v.department_id as emp_department,
                   e.parent_id as emp_parent_id, l.request_date_from, l.request_date_to,
                   l.number_of_days,
                   COALESCE(wet.name->>%s, wet.name->>'en_US', wet.code) as leave_type,
                   COALESCE(SUM(al.number_of_days), 0) AS allocated_days,
                   COALESCE(SUM(CASE WHEN l.state = 'validate' THEN l.number_of_days ELSE 0 END), 0) AS taken_days,
                   COALESCE(SUM(al.number_of_days), 0) - COALESCE(SUM(CASE WHEN l.state = 'validate' THEN l.number_of_days ELSE 0 END), 0) AS balance_days
            FROM hr_employee e
            -- Odoo 20: department_id lives on hr.version, not hr_employee
            LEFT JOIN hr_version v ON v.id = e.current_version_id
            INNER JOIN hr_leave l ON l.employee_id = e.id
            INNER JOIN hr_work_entry_type wet ON l.work_entry_type_id = wet.id
            LEFT JOIN hr_leave_allocation al ON al.employee_id = e.id
                AND al.work_entry_type_id = l.work_entry_type_id
                AND al.state = 'validate'
            WHERE l.state = 'validate' {dept_condition}
            GROUP BY e.id, v.id, wet.id, l.id, wet.name, wet.code
        """

        self.env.cr.execute(query, params)
        leave_data = self.env.cr.dictfetchall()
        filtered_list = []
        for leave in leave_data:
            if not leave.get('request_date_from') or not leave.get('request_date_to'):
                continue
            leave_list = self.generate_date_range(
                leave.get('request_date_from'),
                leave.get('request_date_to')
            )
            for date in leave_list:
                if date in option:
                    filtered_list.append(leave)
                    break

        seen = set()
        final_list = []
        for leave in filtered_list:
            key = (leave.get('hr_leave_type_id'), leave.get('emp_id'))
            if key not in seen:
                seen.add(key)
                final_list.append(leave)

        return {
            'doc_ids': docids,
            'doc_model': 'hr.leave.report',
            'duration': duration,
            'filtered_list': final_list,
        }

    def generate_date_range(self, start_date, end_date):
        """Generate a list of dates within the given range"""
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)
        return date_list
