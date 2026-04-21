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
from odoo import api, fields, models


class HrAttendance(models.Model):
    """Extends Odoo attendance with Hikvision integration fields."""
    _inherit = 'hr.attendance'

    hik_worked_hours = fields.Float(
        string='Worked Hours',
        compute='_compute_hik_worked_hours',
        store=True,
        help='Worked hours calculated from check-in and check-out.'
    )
    adjustment_approval_id = fields.Many2one(
        'attendance.approval',
        string='Adjustment Approval',
        help='Attendance record created from approval adjustment'
    )

    @api.depends('check_in', 'check_out')
    def _compute_hik_worked_hours(self):
        """Calculate worked hours from check-in/out."""
        for rec in self:
            if rec.check_in and rec.check_out and rec.check_out > rec.check_in:
                rec.hik_worked_hours = (rec.check_out - rec.check_in).total_seconds() / 3600.0
            else:
                rec.hik_worked_hours = 0.0

    @api.depends('pending_approval_count')
    def _compute_pending_approval_count(self):
        """Count pending approval requests for employee."""
        for employee in self:
            employee.pending_approval_count = self.env['attendance.approval'].search_count([
                ('employee_id', '=', employee.id),
                ('state', '=', 'submitted')
            ])
