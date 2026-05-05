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
from odoo import fields, models, tools


class DailyAttendance(models.Model):
    """Model to hold data from the biometric device"""
    _name = 'daily.attendance'
    _description = 'Daily Attendance Report'
    _auto = False
    _order = 'punching_time desc'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    punching_day = fields.Date(string='Date')
    attendance_type = fields.Selection([
        ('1', 'Finger'),
        ('15', 'Face'),
        ('2', 'Type_2'),
        ('3', 'Password'),
        ('4', 'Card')
    ], string='Category')

    punch_type = fields.Selection([
        ('0', 'Check In'),
        ('1', 'Check Out'),
        ('2', 'Break Out'),
        ('3', 'Break In'),
        ('4', 'Overtime In'),
        ('5', 'Overtime Out')
    ], string='Punching Type')

    punching_time = fields.Datetime(string='Punching Time')
    company_id = fields.Many2one('res.company', string='Company')

    def init(self):
        """Retrieve the data for attendance report"""
        tools.drop_view_if_exists(self._cr, 'daily_attendance')
        query = """
            CREATE OR REPLACE VIEW daily_attendance AS (
                SELECT
                    id,
                    employee_id,
                    DATE(punching_time AT TIME ZONE 'UTC') as punching_day,
                    attendance_type,
                    punching_time,
                    punch_type,
                    company_id
                FROM zk_machine_attendance
                WHERE punching_time IS NOT NULL
                ORDER BY punching_time DESC
            )
        """
        self._cr.execute(query)