# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from datetime import datetime
from odoo import api, fields, models


class HrEmployee(models.Model):
    """Extends employee with Hikvision integration and attendance tracking."""
    _inherit = 'hr.employee'

    hikvision_number = fields.Char(
        string='Hikvision ID',
        help="Unique employee identifier used for Hikvision device integration."
    )

    attendance_date = fields.Date(
        string='Attendance Date',
        default=fields.Date.context_today,
        help="Select a date to view the employee's attendance records and total worked hours."
    )

    daily_attendance_ids = fields.One2many(
        'hr.attendance',
        'employee_id',
        string='Daily Attendance',
        compute='_compute_daily_attendance_ids',
        help="Attendance records for the selected date."
    )

    total_attendance_hours = fields.Float(
        string='Total Hours (Selected Date)',
        compute='_compute_total_attendance_hours',
        help="Total number of hours worked by the employee on the selected date."
    )

    pending_approval_count = fields.Integer(
        string='Pending Approvals',
        compute='_compute_pending_approval_count',
        help="Number of attendance approval requests waiting for approval."
    )

    @api.depends('attendance_date')
    def _compute_daily_attendance_ids(self):
        """Get attendance records for selected date."""
        for employee in self:
            target_date = employee.attendance_date or fields.Date.today()
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())

            employee.daily_attendance_ids = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', start_of_day),
                ('check_in', '<=', end_of_day)
            ], order='check_in asc')

    @api.depends('attendance_date', 'daily_attendance_ids')
    def _compute_total_attendance_hours(self):
        """Calculate total hours worked on selected date."""
        for employee in self:
            total_hours = 0.0
            for attendance in employee.daily_attendance_ids:
                if attendance.check_in and attendance.check_out and attendance.check_out > attendance.check_in:
                    delta = attendance.check_out - attendance.check_in
                    total_hours += delta.total_seconds() / 3600.0
            employee.total_attendance_hours = total_hours

    def _compute_pending_approval_count(self):
        """Count pending attendance approval requests."""
        for employee in self:
            employee.pending_approval_count = self.env['attendance.approval'].search_count([
                ('employee_id', '=', employee.id),
                ('state', '=', 'submitted')
            ])
