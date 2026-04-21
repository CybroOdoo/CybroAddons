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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AttendanceRejectionWizard(models.TransientModel):
    """Wizard for rejecting attendance with leave options."""

    _name = 'attendance.rejection.wizard'
    _description = 'Attendance Rejection Wizard'

    approval_id = fields.Many2one(
        comodel_name='attendance.approval',
        string='Approval Request',
        required=True,
        help="Attendance approval request that is being rejected."
    )

    rejected_reason = fields.Text(
        string='Rejection Reason',
        required=True,
        help="Reason for rejecting the attendance approval request."
    )

    leave_type = fields.Selection(
        [
            ('half_day', 'Half Day Leave'),
            ('full_day', 'Full Day Leave'),
            ('no_leave', 'No Leave')
        ],
        default='no_leave',
        required=True,
        help="Choose whether a leave should be created for the rejected attendance."
    )

    half_day_period = fields.Selection(
        [('am', 'Morning'), ('pm', 'Afternoon')],
        default='am',
        help="Select the period for half-day leave."
    )

    time_off_type_id = fields.Many2one(
        comodel_name='hr.leave.type',
        string='Time Off Type',
        help="Type of leave that will be created for the employee."
    )

    available_leave_info = fields.Html(
        compute='_compute_available_leave_info',
        help="Displays available leave balances for the employee."
    )

    auto_select_leave = fields.Boolean(
        string='Auto Select Leave Type',
        default=True,
        help="Automatically selects the most suitable leave type based on availability."
    )

    @api.depends('approval_id', 'leave_type')
    def _compute_available_leave_info(self):
        """Compute available leave info for the employee."""
        for rec in self:
            if not rec.approval_id.employee_id or rec.leave_type == 'no_leave':
                rec.available_leave_info = ''
                continue

            duration = 0.5 if rec.leave_type == 'half_day' else 1.0
            allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', rec.approval_id.employee_id.id),
                ('state', '=', 'validate')
            ])

            leaves = [(a.holiday_status_id.name, a.number_of_days - a.leaves_taken)
                      for a in allocations if (a.number_of_days - a.leaves_taken) >= duration]

            if leaves:
                items = ''.join(f'<div class="leave-item"><span class="leave-name">{name}</span>: <span class="leave-balance">{bal:.1f} days</span></div>'
                                for name, bal in leaves)
                rec.available_leave_info = f'<div class="available-leave-container"><h4>Available Leave Balance:</h4>{items}</div>'
            else:
                rec.available_leave_info = '<div class="no-leave-warning"><strong>⚠ No paid leave available</strong><p>Unpaid leave will be assigned.</p></div>'

    @api.onchange('leave_type', 'auto_select_leave')
    def _onchange_leave_type(self):
        """Auto-select leave type based on availability."""
        if self.leave_type in ['half_day', 'full_day'] and self.auto_select_leave:
            self.time_off_type_id = self._get_best_leave_type()

    def _get_best_leave_type(self):
        """Get best matching leave type for the employee."""
        if not self.approval_id.employee_id:
            return None

        duration = 0.5 if self.leave_type == 'half_day' else 1.0
        priorities = ['compensatory', 'comp off', 'paid', 'privilege', 'casual', 'sick', 'unpaid']

        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', self.approval_id.employee_id.id),
            ('state', '=', 'validate')
        ])

        # Find best match by priority
        for priority in priorities:
            for alloc in allocations:
                if priority in alloc.holiday_status_id.name.lower():
                    if alloc.number_of_days - alloc.leaves_taken >= duration:
                        return alloc.holiday_status_id

        return self.env['hr.leave.type'].search([('unpaid', '=', True)], limit=1)

    def action_confirm_rejection(self):
        """Confirm rejection and handle leave creation."""
        self.ensure_one()

        if self.env.user not in self.env.ref('hr.group_hr_manager').users:
            raise UserError(_('Only HR managers can reject requests.'))

        self.approval_id.write({'state': 'rejected', 'rejected_reason': self.rejected_reason})

        if self.leave_type == 'no_leave':
            self.approval_id.message_post(body=_('Rejected: %s') % self.rejected_reason)
            self.approval_id._send_rejection_email()
            return {'type': 'ir.actions.act_window_close'}

        if not self.time_off_type_id:
            raise UserError(_('Please select a Time Off Type.'))

        duration = 0.5 if self.leave_type == 'half_day' else 1.0
        allocation = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', self.approval_id.employee_id.id),
            ('holiday_status_id', '=', self.time_off_type_id.id),
            ('state', '=', 'validate')
        ], limit=1)

        if allocation and not self.time_off_type_id.unpaid:
            remaining = allocation.number_of_days - allocation.leaves_taken
            if remaining < duration:
                raise UserError(_('Insufficient balance for %s.\nAvailable: %.1f | Required: %.1f')
                                % (self.time_off_type_id.name, remaining, duration))

        vals = {
            'name': self.rejected_reason,
            'holiday_status_id': self.time_off_type_id.id,
            'employee_id': self.approval_id.employee_id.id,
            'request_date_from': self.approval_id.date,
            'request_date_to': self.approval_id.date,
            'request_unit_half': self.leave_type == 'half_day',
            'state': 'confirm',
        }

        if self.leave_type == 'half_day':
            vals['request_date_from_period'] = self.half_day_period

        time_off = self.env['hr.leave'].sudo().create(vals)
        time_off.action_approve()

        balance_msg = ''
        if allocation and not self.time_off_type_id.unpaid:
            new_bal = allocation.number_of_days - allocation.leaves_taken
            balance_msg = f'<br/>Remaining: {new_bal:.1f} days'

        self.approval_id.message_post(
            body=_('Rejected: %s<br/>%s %s created & approved.%s') % (
                self.rejected_reason,
                'Half day' if self.leave_type == 'half_day' else 'Full day',
                self.time_off_type_id.name,
                balance_msg
            )
        )

        self.approval_id._send_rejection_email()

        return {'type': 'ir.actions.act_window_close'}
