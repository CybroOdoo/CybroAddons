# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models


class AttendanceRegular(models.Model):
    """Model to record regularization attendance"""
    _name = 'attendance.regular'
    _rec_name = 'employee_id'
    _description = 'Attendance Regularization'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_employee_id(self):
        """Get the ID of the currently logged-in employee"""
        employee_rec = self.env['hr.employee'].search([
            ('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    reg_category = fields.Many2one('reg.categories', string='Regularization Category',
                                   required=True, help='Choose the category of attendance regularization')
    from_date = fields.Datetime(string='From Date', required=True,
                                help='Start Date')
    to_date = fields.Datetime(string='To Date', required=True,
                              help='End Date')
    reg_reason = fields.Text(string='Reason', required=True,
                             help='Reason for the attendance regularization')
    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  default=_default_employee_id, readonly=True,
                                  required=True, help='Employee')
    state = fields.Selection([('draft', 'Draft'),
                              ('requested', 'Requested'),
                              ('reject', 'Rejected'),
                              ('approved', 'Approved')], default='draft',
                             copy=False, track_visibility='onchange',
                             string='State', help='Status of record')
    def action_submit(self):
        """Change state to 'requested' upon submission"""
        self.ensure_one()
        self.sudo().write({
            'state': 'requested'
        })
        return

    def action_approve(self):
        """Approve the attendance regularization"""
        self.write({
            'state': 'approved'
        })
        vals = {
            'check_in': self.from_date,
            'check_out': self.to_date,
            'employee_id': self.employee_id.id,
            'regularization': True
        }
        self.env['hr.attendance'].sudo().create(vals)
        return

    def action_reject(self):
        """Reject the attendance regularization"""
        self.write({
            'state': 'reject'
        })
        return
