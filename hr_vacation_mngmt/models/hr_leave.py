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
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrLeave(models.Model):
    """Inherited model for managing HR Leave requests."""
    _inherit = 'hr.leave'

    remaining_leaves = fields.Float(
        string='Remaining Legal Leaves',
        compute='_compute_remaining_leaves',
        help="Remaining legal leaves"
    )
    overlapping_leaves_ids = fields.Many2many('hr.leave',
                                              compute='_compute_overlapping_leaves_ids',
                                              string='Overlapping Leaves',
                                              help="Overlapping leaves of"
                                                   " employees.")
    pending_task_ids = fields.One2many('pending.task',
                                       'leave_id',
                                       string='Pending Tasks',
                                       help="Details of pending tasks")
    holiday_managers_ids = fields.Many2many('res.users',
                                            compute='_compute_holiday_managers_ids',
                                            help="Responsible holiday managers")
    flight_ticket_ids = fields.One2many('hr.flight.ticket',
                                        'leave_id',
                                        string='Flight Ticket',
                                        help="Flight ticket Details")
    expense_account_id = fields.Many2one('account.account',
                                         string='Expense Account',
                                         help='Expense account to account the '
                                              'flight expenses.')
    leave_salary = fields.Selection([('0', 'Basic'), ('1', 'Gross')],
                                    string='Leave Salary',
                                    help='Details about leave salary of'
                                         ' employee.')

    @api.depends('overlapping_leaves_ids', 'date_from', 'date_to')
    def _compute_overlapping_leaves_ids(self):
        """Compute function over overlapping leaves"""
        for rec in self:
            if rec.date_from and rec.date_to:
                overlap_leaves = []
                from_date = rec.date_from
                to_date = rec.date_to
                differ_days = (to_date + timedelta(days=1) - from_date).days
                [str(from_date + timedelta(days=day)) for day in range(differ_days)]
                leaves = rec.env['hr.leave'].search([('state', '=', 'validate'),
                                                      ('department_id', '=',
                                                       rec.department_id.id)])
                other_leaves = leaves - rec
                for leave in other_leaves:
                    frm_dte = leave.date_from
                    to_dte = leave.date_to
                    differ_days = (to_dte + timedelta(days=1) - frm_dte).days
                    leave_dates = [str(frm_dte + timedelta(days=i)) for i in
                                   range(differ_days)]
                    if set(leave_dates).intersection(set(leave_dates)):
                        overlap_leaves.append(leave.id)
                rec.update({'overlapping_leaves_ids': [(6, 0, overlap_leaves)]})
            else:
                rec.overlapping_leaves_ids = False

    def action_approve(self):
        """This method is used to approve leave requests. It checks if the
        current user has the necessary permissions, ensures that the leave
        request is in the 'confirm' state, and takes appropriate action
        based on the presence of pending tasks."""
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(
                _('Only an HR Officer or Manager can approve leave requests.'))
        for holiday in self:
            if holiday.state != 'confirm':
                raise UserError(
                    _('Leave request must be confirmed ("To Approve") in '
                      'order to approve it.'))
            if holiday.pending_task_ids:
                if holiday.user_id:
                    ctx = dict(self.env.context or {})
                    ctx.update({
                        'default_leave_req_id': self.id,
                    })
                    return {
                        'name': _('Re-Assign Task'),
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'task.reassign',
                        'target': 'new',
                        'context': ctx,
                    }
            else:
                holiday._action_validate()

    def action_book_ticket(self):
        """Open the form view to book a flight ticket for the current
         leave request."""
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(
                _('Only an HR Officer or Manager can book flight tickets.'))
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_leave_id': self.id,
        })
        return {
            'name': _('Book Flight Ticket'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'hr_vacation_mngmt.view_hr_book_flight_ticket_form').id,
            'res_model': 'hr.flight.ticket',
            'target': 'new',
            'context': ctx,
        }

    def _compute_holiday_managers_ids(self):
        """Retrieve the IDs of users belonging to the
         'Holiday Managers' group."""
        self.holiday_managers_ids = self.env.ref(
            'hr_holidays.group_hr_holidays_manager').users

    def action_view_flight_ticket(self):
        """Open the form view for the first flight ticket associated
         with this employee."""
        return {
            'name': _('Flight Ticket'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.flight.ticket',
            'target': 'current',
            'res_id': self.flight_ticket_ids[0].id,
        }

    @api.model
    def send_leave_reminder(self):
        """Send leave reminders to holiday managers for validated leave
         requests."""
        leave_request = self.env['hr.leave'].search(
            [('state', '=', 'validate')])
        leave_reminder = self.env['ir.config_parameter'].sudo().get_param(
            'leave_reminder')
        reminder_day_before = int(
            self.env['ir.config_parameter'].sudo().get_param(
                'reminder_day_before'))
        mail_template = self.env.ref(
            'hr_vacation_mngmt.email_template_hr_leave_reminder_mail')
        holiday_managers = self.env.ref(
            'hr_holidays.group_hr_holidays_manager').users
        if leave_reminder:
            for request in leave_request:
                if request.date_from:
                    from_date = request.date_from
                    if reminder_day_before == 0:
                        prev_reminder_day = request.date_from
                    else:
                        prev_reminder_day = from_date - timedelta(
                            days=reminder_day_before)
                    if prev_reminder_day.date() == fields.Date.today():
                        for manager in holiday_managers:
                            template = mail_template.sudo().with_context(
                                email_to=manager.email,
                            )
                            email_template_obj = self.env[
                                'mail.template'].browse(template.id)
                            values = email_template_obj.generate_email(
                                request.id,
                                ['subject', 'body_html', 'email_from',
                                 'email_to', 'partner_to', 'email_cc',
                                 'reply_to', 'scheduled_date'])
                            values['email_to'] = manager.email
                            msg_id = self.env['mail.mail'].create(values)
                            if msg_id:
                                msg_id._send()

    @api.depends('employee_id', 'holiday_status_id')
    def _compute_remaining_leaves(self):
        for leave in self:
            if not leave.employee_id or not leave.holiday_status_id:
                leave.remaining_leaves = 0.0
                continue

            # Get the employee's remaining leaves for this leave type
            allocation_data = leave.holiday_status_id.get_allocation_data(
                leave.employee_id,
                target_date=fields.Date.context_today(self)
            )

            # Get the data for this specific leave type
            leave_type_data = next(
                (data for data in allocation_data[leave.employee_id]
                 if data[0] == leave.holiday_status_id.name),
                None
            )

            if leave_type_data and len(leave_type_data) > 1:
                leave.remaining_leaves = leave_type_data[1].get('virtual_remaining_leaves', 0.0)
            else:
                leave.remaining_leaves = 0.0