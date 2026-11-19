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
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytz

from odoo import api, fields, models
from odoo.tools import date_utils


class HrLeave(models.Model):
    """Inherit the model hr.leave to introduce supplementary functionality
    aimed at incorporating specific employee details."""
    _inherit = 'hr.leave'

    def _prepare_employee_data(self, employee):
        """Function to prepare employee data for the dashboard"""
        if not employee:
            return {}
        return {
            'id': employee.id,
            'name': employee.name,
            'job_id': employee.job_id.name,
            'approval_status_count': self.get_approval_status_count(employee.id)
        }

    @api.model
    def get_current_employee(self):
        """This function fetches current employee details in a dictionary"""
        employee_id = self.env.context.get('employee_id')
        current_employee = self.env['hr.employee'].browse(employee_id) if employee_id else self.env.user.employee_id
        if not current_employee:
            return {}
        # Odoo 20 Binary fields return a BinaryValue (or False when empty).
        image = current_employee.image_1920
        image_1920 = image.to_base64() if image else False
        return {
            'id': current_employee.id,
            'name': current_employee.name,
            'job_id': current_employee.job_id.id,
            'image_1920': image_1920,
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
        current date by searching for validated leave requests. It returns
        a list of dictionaries containing the employee's name, employee_id,
        date_from, and date_to."""
        employee_id = self.env.context.get('employee_id')
        current_employee = self.env['hr.employee'].browse(employee_id) if employee_id else self.env.user.employee_id
        if not current_employee or not current_employee.child_ids:
            return []
        child_ids = current_employee.child_ids.ids
        # "Today" is the manager's local calendar day, so a leave that starts
        # later today (e.g. 08:00) already counts, not only leaves running now.
        tz = self._dashboard_tz(current_employee)
        local_today = fields.Datetime.now().replace(tzinfo=pytz.utc).astimezone(tz).date()
        day_start = tz.localize(datetime.combine(local_today, time.min))
        day_end = day_start + timedelta(days=1)
        leaves = self.env['hr.leave'].search([
            ('employee_id', 'in', child_ids),
            ('state', '=', 'validate'),
            ('date_from', '<', day_end.astimezone(pytz.utc).replace(tzinfo=None)),
            ('date_to', '>', day_start.astimezone(pytz.utc).replace(tzinfo=None)),
        ], order='date_from')
        absentees = {}
        for leave in leaves:
            # One row per employee: the template keys the list on employee_id.
            absentees.setdefault(leave.employee_id.id, {
                'employee_id': leave.employee_id.id,
                'name': leave.employee_id.name,
                'date_from': leave.date_from,
                'date_to': leave.date_to,
            })
        return list(absentees.values())

    @api.model
    def _safe_tz(self, tz_name):
        """``pytz`` timezone for ``tz_name``, falling back to UTC when it is
        empty or unknown."""
        try:
            return pytz.timezone(tz_name or 'UTC')
        except pytz.UnknownTimeZoneError:
            return pytz.utc

    def _dashboard_tz(self, employee):
        """Timezone used for the dashboard's notion of "today"."""
        return self._safe_tz(
            (employee.tz if employee else False) or self.env.user.tz)

    def _period_domain(self, period):
        """Domain on hr.leave for leaves overlapping ``period``
        (today / this_week / this_month / this_year); empty for anything else,
        i.e. no date restriction. The period is the *dashboard viewer's*
        (context employee, else current user), so every row in the table and
        the "On leave today" box share the same notion of today."""
        if period not in ('today', 'this_week', 'this_month', 'this_year'):
            return []
        employee_id = self.env.context.get('employee_id')
        viewer = self.env['hr.employee'].browse(employee_id) if employee_id \
            else self.env.user.employee_id
        tz = self._dashboard_tz(viewer)
        today = fields.Datetime.now().replace(tzinfo=pytz.utc).astimezone(tz).date()
        if period == 'today':
            start = end = today
        else:
            granularity = {'this_week': 'week', 'this_month': 'month', 'this_year': 'year'}[period]
            start = date_utils.start_of(today, granularity)
            end = date_utils.end_of(today, granularity)
        return [('request_date_from', '<=', end), ('request_date_to', '>=', start)]

    @api.model
    def get_current_shift(self):
        """ This function fetches current employee's current shift"""
        employee_id = self.env.context.get('employee_id')
        current_employee = self.env['hr.employee'].browse(employee_id) if employee_id else self.env.user.employee_id
        if not current_employee or not current_employee.resource_calendar_id:
            return False
        tz = ZoneInfo(self._safe_tz(
            current_employee.tz or self.env.context.get('tz')).zone)
        now = fields.Datetime.now().replace(tzinfo=ZoneInfo('UTC')).astimezone(tz)
        day_start = datetime.combine(now.date(), time.min, tzinfo=tz)
        # Odoo 20 attendances have no name and may be fixed hours, duration
        # based or dated (variable schedules): let the calendar expand today's
        # work intervals, each carrying its attendance.
        intervals = current_employee.resource_calendar_id._attendance_intervals_batch(
            day_start, day_start + timedelta(days=1))[False]
        periods = dict(self.env['resource.calendar.attendance']._fields[
            'day_period']._description_selection(self.env))
        for start, stop, attendance in intervals:
            if start <= now < stop:
                return periods.get(attendance[:1].day_period) or False
        return False

    @api.model
    def get_upcoming_holidays(self):
        """ This function fetches upcoming holidays"""
        employee_id = self.env.context.get('employee_id')
        current_employee = self.env['hr.employee'].browse(employee_id) if employee_id else self.env.user.employee_id
        today = fields.Date.context_today(self)
        domain = [
            ('resource_id', '=', False),
            ('date_to', '>=', fields.Datetime.to_datetime(today)),
        ]
        if current_employee and current_employee.company_id:
            domain.append(('company_id', 'in', [False, current_employee.company_id.id]))
        holidays = self.env['resource.calendar.leaves'].search(domain, order='date_from asc')
        default_tz = (current_employee.tz if current_employee else False) \
            or self.env.user.tz

        def local_date(holiday, value):
            """Datetimes are stored in UTC; convert to the holiday company's
            (or employee's) timezone before taking the date, otherwise a
            holiday starting at local midnight shows up one day early.
            Odoo 20 has no tz on resource.calendar, it lives on res.company."""
            tz = self._safe_tz(holiday.company_id.tz or default_tz)
            return str(pytz.utc.localize(value).astimezone(tz).date())

        return [
            {
                'id': h.id,
                'name': h.name,
                'date_from': local_date(h, h.date_from),
                'date_to': local_date(h, h.date_to),
            }
            for h in holidays
        ]

    @api.model
    def get_approval_status_count(self, current_employee, period=False):
        """Approved / to approve / refused leave counts of an employee,
        optionally limited to leaves overlapping ``period``."""
        if not current_employee:
            return {'validate_count': 0, 'confirm_count': 0, 'refuse_count': 0}
        base = [('employee_id', '=', current_employee)] + self._period_domain(period)
        Leave = self.env['hr.leave']
        return {
            'validate_count': Leave.search_count(base + [('state', '=', 'validate')]),
            'confirm_count': Leave.search_count(base + [('state', '=', 'confirm')]),
            'refuse_count': Leave.search_count(base + [('state', '=', 'refuse')]),
        }

    @api.model
    def get_team_approval_status_counts(self, employee_ids, period=False):
        """Approval counts for several employees at once, keyed by employee
        id, for the My Team table's period filter."""
        return {
            employee_id: self.get_approval_status_count(employee_id, period)
            for employee_id in employee_ids or []
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
                'leave_type_id': leave.work_entry_type_id.id,
                'leave_type': leave.work_entry_type_id.name,
                'number_of_days': leave.number_of_days
            }
            for leave in leaves
        ]
        return all_validated_leaves
