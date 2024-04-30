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
import pytz
from odoo import api, fields, models


class HrLeave(models.Model):
    """Inherit the model hr.leave to introduce supplementary functionality
    aimed at incorporating specific employee details."""
    _inherit = 'hr.leave'

    def _prepare_employee_data(self, employee):
        """Function to prepare employee data for the dashboard"""
        return {
            'id': employee.id,
            'name': employee.name,
            'job_id': employee.job_id.name,
            'approval_status_count': self.get_approval_status_count(employee.id)
        }

    @api.model
    def get_current_employee(self):
        """This function fetches current employee details in a dictionary"""
        current_employee = self.env.user.employee_ids
        return {
            'id': current_employee.id,
            'name': current_employee.name,
            'job_id': current_employee.job_id.id,
            'image_1920': current_employee.image_1920,
            'work_email': current_employee.work_email,
            'work_phone': current_employee.work_phone,
            'resource_calendar_id': current_employee.resource_calendar_id.name,
            'link': '/mail/view?model=%s&res_id=%s' % (
                'hr.employee.public', current_employee.id,),
            'department_id': current_employee.department_id.name,
            'company': current_employee.company_id.name,
            'job_position': current_employee.job_id.name,
            'parent_id': current_employee.parent_id.ids,
            'child_ids': current_employee.child_ids.ids,
            'child_all_count': current_employee.child_all_count,
            'manager': self._prepare_employee_data(
                current_employee.parent_id) if (
                current_employee.parent_id) else {},
            'manager_all_count': len(current_employee.parent_id.ids),
            'children': [self._prepare_employee_data(child) for child in
                         current_employee.child_ids if
                         child != current_employee],
        }

    @api.model
    def get_absentees(self):
        """The function retrieves a list of employees who are absent on the
        current date by querying the hr_leave table and comparing the
        date_from and date_to fields of validated leave requests. It returns
        a list of dictionaries containing the employee's name, employee_id,
        date_from, and date_to"""
        current_employee = self.env.user.employee_ids
        children = [self._prepare_employee_data(child) for child in
                    current_employee.child_ids if
                    child != current_employee]
        child_list = [child.get('id') for child in children]
        if len(child_list) > 1:
            query = "SELECT employee_id,name,date_from,date_to FROM hr_leave " \
                    "INNER JOIN hr_employee ON hr_leave.employee_id = " \
                    "hr_employee.id WHERE state = 'validate' AND " \
                    "employee_id in %s" % str(tuple(child_list))
            self._cr.execute(query)
        elif len(child_list) == 1:
            query = "SELECT employee_id,name,date_from,date_to FROM hr_leave " \
                    "INNER JOIN hr_employee ON hr_leave.employee_id = " \
                    "hr_employee.id WHERE state = 'validate' AND " \
                    "employee_id = %s" % child_list[0]
            self._cr.execute(query)
        leave = self._cr.dictfetchall()
        absentees = [
            leave[leave_date] for leave_date in range(len(leave))
            if leave[leave_date].get('date_from') <= fields.datetime.now() <= leave[
                leave_date].get('date_to')
        ]
        return absentees

    @api.model
    def get_current_shift(self):
        """ This function fetches current employee's current shift"""
        current_employee = self.env.user.employee_ids
        employee_tz = current_employee.tz or self.env.context.get('tz')
        employee_pytz = pytz.timezone(employee_tz) if employee_tz else pytz.utc
        employee_datetime = fields.datetime.now().astimezone(employee_pytz)
        hour = employee_datetime.strftime("%H")
        minute = employee_datetime.strftime("%M")
        day = employee_datetime.strftime("%A")
        time = hour + '.' + minute
        day_num = '0' if day == 'Monday' else '1' if day == 'Tuesday' \
            else '2' if day == 'Wednesday' else '3' if day == 'Thursday' \
            else '4' if day == 'Friday' else '5' if day == 'Saturday' else '6'
        for shift in current_employee.resource_calendar_id.attendance_ids:
            if shift.dayofweek == day_num and shift.hour_from <= float(
                    time) <= shift.hour_to:
                return shift.name
        return False

    @api.model
    def get_upcoming_holidays(self):
        """ This function fetches upcoming holidays"""
        current_employee = self.env.user.employee_ids
        employee_tz = current_employee.tz or self.env.context.get('tz')
        employee_pytz = pytz.timezone(employee_tz) if employee_tz else pytz.utc
        employee_datetime = fields.datetime.now().astimezone(employee_pytz)
        query = "SELECT * FROM public.resource_calendar_leaves WHERE " \
                "resource_id is null"
        self._cr.execute(query)
        holidays = self._cr.dictfetchall()
        upcoming_holidays = [holiday for holiday in holidays if
                             employee_datetime.date() < holiday.get(
                                 'date_to').date()]
        return upcoming_holidays

    @api.model
    def get_approval_status_count(self, current_employee):
        """ This function fetches approval status count"""
        return {
            'validate_count': self.env['hr.leave'].search_count([
                ('employee_id', '=', current_employee),
                ('state', '=', 'validate')
            ]),
            'confirm_count': self.env['hr.leave'].search_count([
                ('employee_id', '=', current_employee),
                ('state', '=', 'confirm')
            ]),
            'refuse_count': self.env['hr.leave'].search_count([
                ('employee_id', '=', current_employee),
                ('state', '=', 'refuse')
            ])
        }

    @api.model
    def get_all_validated_leaves(self):
        """ This function fetches all validated leaves"""
        leaves = self.env['hr.leave'].search([('state', '=', 'validate')])
        all_validated_leaves = [
            {
                'id': leave.id,
                'employee_id': leave.employee_id.id,
                'employee_name': leave.employee_id.name,
                'request_date_from': leave.request_date_from,
                'request_date_to': leave.request_date_to,
                'leave_type_id': leave.holiday_status_id.id,
                'leave_type': leave.holiday_status_id.name,
                'number_of_days': leave.number_of_days
            }
            for leave in leaves
        ]
        return all_validated_leaves
