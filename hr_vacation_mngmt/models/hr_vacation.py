# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrLeaveRequest(models.Model):
    _inherit = 'hr.holidays'

    remaining_leaves = fields.Float(string='Remaining Legal Leaves', related='employee_id.remaining_leaves')
    overlapping_leaves = fields.Many2many('hr.holidays', compute='get_overlapping_leaves', string='Overlapping Leaves')
    pending_tasks = fields.One2many('pending.task', 'leave_id', string='Pending Tasks')
    holiday_managers = fields.Many2many('res.users', compute='get_hr_holiday_managers')
    flight_ticket = fields.One2many('hr.flight.ticket', 'leave_id', string='Flight Ticket')

    @api.one
    def get_overlapping_leaves(self):
        if self.type == 'remove' and self.date_from and self.date_to:
            overlap_leaves = []
            from_date = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S').date()
            to_date = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S').date()
            r = (to_date + timedelta(days=1) - from_date).days
            leave_dates = [str(from_date + timedelta(days=i)) for i in range(r)]
            leaves = self.env['hr.holidays'].search([('state', '=', 'validate'), ('type', '=', 'remove'),
                                                     ('department_id', '=', self.department_id.id)])
            other_leaves = leaves - self
            for leave in other_leaves:
                frm_dte = datetime.strptime(leave.date_from, '%Y-%m-%d %H:%M:%S').date()
                to_dte = datetime.strptime(leave.date_to, '%Y-%m-%d %H:%M:%S').date()
                r = (to_dte + timedelta(days=1) - frm_dte).days
                leave_dtes = [str(frm_dte + timedelta(days=i)) for i in range(r)]
                if set(leave_dtes).intersection(set(leave_dates)):
                    overlap_leaves.append(leave.id)
            self.update({'overlapping_leaves': [(6, 0, overlap_leaves)]})

    @api.multi
    def action_approve(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state != 'confirm':
                raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))

            if holiday.pending_tasks:
                if holiday.user_id:
                    ctx = dict(self.env.context or {})
                    ctx.update({
                        'default_leave_req_id': self.id,
                    })
                    return {
                        'name': _('Re-Assign Task'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'task.reassign',
                        'target': 'new',
                        'context': ctx,
                    }
                else:
                    raise UserError(_('Please configure user for the employee %s') % (holiday.employee_id.name,))
            else:
                if holiday.double_validation:
                    return holiday.write({'state': 'validate1', 'manager_id': manager.id if manager else False})
                else:
                    holiday.action_validate()

    def book_ticket(self):
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can book flight tickets.'))
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_employee_id': self.employee_id.id,
            'default_leave_id': self.id,
        })
        return {
            'name': _('Book Flight Ticket'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('hr_vacation_mngmt.view_hr_book_flight_ticket_form').id,
            'res_model': 'hr.flight.ticket',
            'target': 'new',
            'context': ctx,
        }

    @api.one
    def get_hr_holiday_managers(self):
        self.holiday_managers = self.env.ref('hr_holidays.group_hr_holidays_manager').users

    def view_flight_ticket(self):
        return {
            'name': _('Flight Ticket'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.flight.ticket',
            'target': 'current',
            'res_id': self.flight_ticket[0].id,
        }

    @api.model
    def send_leave_reminder(self):
        leave_request = self.env['hr.holidays'].search([('type', '=', 'remove'), ('state', '=', 'validate')])
        leave_reminder = self.env['ir.config_parameter'].sudo().get_param('leave_reminder')
        reminder_day_before = int(self.env['ir.config_parameter'].sudo().get_param('reminder_day_before'))
        mail_template = self.env.ref('hr_vacation_mngmt.email_template_hr_leave_reminder_mail')
        holiday_managers = self.env.ref('hr_holidays.group_hr_holidays_manager').users
        today = date.today()
        if leave_reminder:
            for request in leave_request:
                if request.date_from:
                    from_date = datetime.strptime(request.date_from, '%Y-%m-%d %H:%M:%S').date()
                    if reminder_day_before == 0:
                        prev_reminder_day = request.date_from
                    else:
                        prev_reminder_day = from_date - timedelta(days=reminder_day_before)
                    if prev_reminder_day == today:
                        for manager in holiday_managers:
                            template = mail_template.sudo().with_context(
                                email_to=manager.email,
                            )
                            template.send_mail(request.id, force_send=True)


class PendingTask(models.Model):
    _name = 'pending.task'

    name = fields.Char(string='Task', required=True)
    leave_id = fields.Many2one('hr.holidays', string='Leave Request')
    dept_id = fields.Many2one('hr.department', string='Department', related='leave_id.department_id')
    project_id = fields.Many2one('project.project', string='Project', required=True)
    description = fields.Text(string='Description')
    assigned_to = fields.Many2one('hr.employee', string='Assigned to',
                                  domain="[('department_id', '=', dept_id)]")
    unavailable_employee = fields.Many2many('hr.employee', string='Unavailable Employees',
                                            compute='get_unavailable_employee')

    @api.one
    def get_unavailable_employee(self):
        unavail_emp = []
        for leave in self.leave_id.overlapping_leaves:
            unavail_emp.append(leave.employee_id.id)
        self.update({'unavailable_employee': unavail_emp})


class HrVacationConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    leave_reminder = fields.Boolean(string='Leave Reminder Email', help="Send leave remainder emails to hr managers")
    reminder_day_before = fields.Integer(string='Reminder Day Before')
    default_expense_account = fields.Many2one('account.account', string='Travel Expense Account')

    def get_values(self):
        res = super(HrVacationConfigSettings, self).get_values()
        res.update(
            leave_reminder=self.env['ir.config_parameter'].sudo().get_param('leave_reminder'),
            reminder_day_before=int(self.env['ir.config_parameter'].sudo().get_param('reminder_day_before')),
            default_expense_account=int(self.env['ir.config_parameter'].sudo().get_param('travel_expense_account'))
        )
        return res

    def set_values(self):
        super(HrVacationConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('leave_reminder', self.leave_reminder)
        self.env['ir.config_parameter'].sudo().set_param('reminder_day_before', self.reminder_day_before)
        self.env['ir.config_parameter'].sudo().set_param('travel_expense_account', self.default_expense_account.id)
