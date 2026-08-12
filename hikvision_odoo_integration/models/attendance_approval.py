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
from datetime import datetime, date, time as dt_time
from odoo import api, fields, models, _


class AttendanceApproval(models.Model):
    """
    Manages attendance approval requests for employees with insufficient work hours.
    This model handles the creation, submission, approval, and rejection of attendance
    adjustment requests, including email notifications and cron job automation.
    """
    _name = 'attendance.approval'
    _description = 'Attendance Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True,
        readonly=True,
        help="Employee for whom the attendance approval request is created."
    )

    date = fields.Date(
        string='Date',
        required=True,
        readonly=True,
        help="Date for which the attendance hours are evaluated."
    )

    total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_total_hours',
        store=True,
        help="Total number of worked hours calculated for the selected date."
    )

    minimum_hours = fields.Float(
        string='Minimum Hours',
        default=lambda self: float(
            self.env['ir.config_parameter'].sudo().get_param(
                'hikvision_odoo_integration.minimum_working_hours', '8.0'
            )
        ),
        readonly=True,
        help="Minimum required working hours configured in system settings."
    )

    reason = fields.Text(
        string='Reason',
        tracking=True,
        help="Reason provided by the employee for insufficient working hours."
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        help="Current state of the attendance approval request."
    )

    rejected_reason = fields.Text(
        string='Rejected Reason',
        tracking=True,
        help="Reason provided by the HR manager when rejecting the request."
    )
    active = fields.Boolean(default=True)

    @api.constrains('date')
    def _check_date(self):
        """
        Validates that the date field is not empty for attendance approval records.
        Raises a ValidationError if the date is missing.
        """
        for record in self:
            if not record.date:
                raise models.ValidationError(_('The date field cannot be empty.'))

    @api.depends('employee_id', 'date')
    def _compute_total_hours(self):
        """
        Computes the total hours worked by an employee for a specific date.
        It searches for 'hr.attendance' records for the employee on the given date
        and sums their 'hik_worked_hours'.
        """
        for record in self:
            if not record.date or not isinstance(record.date, date):
                record.total_hours = 0.0
                continue
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', record.employee_id.id),
                ('check_in', '>=', datetime.combine(record.date, dt_time.min)),
                ('check_in', '<=', datetime.combine(record.date, dt_time.max)),
                ('adjustment_approval_id', '=', False),
            ])
            record.total_hours = sum((a.hik_worked_hours or 0.0) for a in attendances)

    def action_submit(self):
        """
        Submits the attendance approval request to HR managers.
        Changes the state to 'submitted' and creates an activity for HR managers
        to review the request. Requires a reason to be provided.
        """
        self.ensure_one()
        if not self.reason:
            raise models.UserError(_('Please provide a reason before submitting.'))
        self.write({'state': 'submitted'})
        hr_managers = self.env.ref('hr.group_hr_manager').users
        for manager in hr_managers:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                note=_('Attendance approval request from %s for %s requires your review.') % (
                    self.employee_id.name, self.date),
                user_id=manager.id
            )

    def action_approve(self):
        """
        Approves the attendance request.
        This action can only be performed by HR managers. It changes the state to 'approved',
        posts a message, and sends an approval email to the employee.
        """
        self.ensure_one()
        if self.env.user not in self.env.ref('hr.group_hr_manager').users:
            raise models.AccessError(_('Only HR managers can approve attendance requests.'))

        self.write({'state': 'approved'})
        self.message_post(body=_('Attendance approval approved by %s.') % self.env.user.name)
        self._send_approval_email()

    def action_reject(self):
        """
        Opens a wizard for HR managers to reject the attendance approval request.
        This action can only be performed by HR managers. It returns an action
        to open the 'attendance.rejection.wizard' form.
        """
        self.ensure_one()
        if self.env.user not in self.env.ref('hr.group_hr_manager').users:
            raise models.AccessError(_('Only HR managers can reject attendance requests.'))

        return {
            'name': _('Reject Attendance Approval'),
            'type': 'ir.actions.act_window',
            'res_model': 'attendance.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_approval_id': self.id,
            }
        }

    def _send_approval_email(self):
        """
        Sends an approval email to the employee.
        This method checks if the employee has a work email and then sends
        the 'email_template_attendance_approved' email template.
        """
        self.ensure_one()
        if not self.employee_id.work_email:
            return

        template = self.env.ref('hikvision_odoo_integration.email_template_attendance_approved',
                                raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_rejection_email(self):
        """
        Sends a rejection email to the employee.
        This method checks if the employee has a work email and then sends
        the 'email_template_attendance_rejected' email template.
        """
        self.ensure_one()
        if not self.employee_id.work_email:
            return

        template = self.env.ref('hikvision_odoo_integration.email_template_attendance_rejected',
                                raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    @api.model
    def cron_check_attendance_approvals(self):
        """
        Cron job to automatically create attendance approval requests.
        It identifies employees who have worked less than the minimum required hours
        for the current day and creates a 'draft' approval request for them,
        then sends a notification. This runs only if HR approval is enabled.
        """
        if not self.env['ir.config_parameter'].sudo().get_param('hikvision_odoo_integration.enable_hr_approval'):
            return
        min_hours = float(
            self.env['ir.config_parameter'].sudo().get_param('hikvision_odoo_integration.minimum_working_hours', '8.0'))
        today = fields.Date.today()
        employees = self.env['hr.employee'].search([])
        for employee in employees:
            existing_approval = self.search([
                ('employee_id', '=', employee.id),
                ('date', '=', today),
            ])
            if existing_approval:
                continue
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', datetime.combine(today, dt_time.min)),
                ('check_in', '<=', datetime.combine(today, dt_time.max)),
                ('adjustment_approval_id', '=', False),
            ])
            total_hours = sum((a.hik_worked_hours or 0.0) for a in attendances)
            if attendances and total_hours < min_hours:
                approval = self.create({
                    'employee_id': employee.id,
                    'date': today,
                })
                approval._send_notification_later()

    def _send_notification_later(self):
        """
        Sends an email notification to the employee to submit a reason for their attendance shortfall.
        Sets the approval request state to 'draft' and sends the
        'email_template_attendance_approval_request' email template.
        """
        self.ensure_one()
        self.write({'state': 'draft'})
        template = self.env.ref('hikvision_odoo_integration.email_template_attendance_approval_request',
                                raise_if_not_found=True)
        template.send_mail(self.id, force_send=True)

    @api.model
    def _cron_send_notifications(self):
        """
        Cron job to check for attendance shortfalls and send notifications to employees.
        First, it calls `cron_check_attendance_approvals` to create new requests.
        Then, for existing 'draft' approvals with shortfalls, it ensures a notification
        email is sent if one hasn't been sent already.
        """
        self.cron_check_attendance_approvals()
        approvals = self.search([('state', '=', 'draft')])
        for approval in approvals:
            if approval.total_hours < approval.minimum_hours and approval.employee_id.work_email:
                mail = self.env['mail.mail'].search([
                    ('model', '=', 'attendance.approval'),
                    ('res_id', '=', approval.id),
                    ('state', '=', 'draft')
                ], limit=1)
                if not mail:
                    approval._send_notification_later()
                self.env['mail.mail'].process_email_queue()
