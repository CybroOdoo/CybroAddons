# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import _, api, fields, models


class HrEmployee(models.Model):
    """Extend the HR Employee model for ZKTeco attendance integration."""
    _inherit = 'hr.employee'

    zkteco_user_id = fields.Char(
        string='ZKTeco User ID', index=True, copy=False,
        groups='hr.group_hr_user',
        help='User PIN of this employee on the ZKTeco biometric devices. '
             'Punches with this ID are recorded as attendance for this '
             'employee. The Badge ID is used as a fallback.',
    )
    zkteco_device_user_ids = fields.One2many(
        'zkteco.device.user', 'employee_id', string='Biometric Device Users',
        groups='hr_attendance.group_hr_attendance_officer',
    )
    zkteco_template_ids = fields.One2many(
        'zkteco.biometric.template', 'employee_id', string='Biometric Data',
        groups='hr_attendance.group_hr_attendance_officer',
    )
    zkteco_device_count = fields.Integer(
        compute='_compute_zkteco_counts',
        groups='hr_attendance.group_hr_attendance_officer',
    )
    zkteco_template_count = fields.Integer(
        string='Enrolled Templates', compute='_compute_zkteco_counts',
        groups='hr_attendance.group_hr_attendance_officer',
    )

    @api.depends('zkteco_device_user_ids', 'zkteco_template_ids')
    def _compute_zkteco_counts(self):
        """Compute the ZKTeco device user and template counts for each employee."""
        for employee in self:
            employee.zkteco_device_count = len(employee.zkteco_device_user_ids)
            employee.zkteco_template_count = len(employee.zkteco_template_ids)

    def action_zkteco_view_punches(self):
        """Open the ZKTeco punch logs associated with the current employee."""
        self.ensure_one()
        return {
            'name': _('Punch Logs'),
            'type': 'ir.actions.act_window',
            'res_model': 'zkteco.attendance.log',
            'view_mode': 'list,form,graph,pivot',
            'domain': [('employee_id', '=', self.id)],
        }

    def action_zkteco_export_to_device(self):
        """Open the export wizard pre-filled with these employees."""
        return {
            'name': _('Export to Biometric Device'),
            'type': 'ir.actions.act_window',
            'res_model': 'zkteco.export.employees.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_employee_ids': self.ids},
        }
