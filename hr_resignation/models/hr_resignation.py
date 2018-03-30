# -*- coding: utf-8 -*-
import datetime
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
date_format = "%Y-%m-%d"


class HrResignation(models.Model):
    _name = 'hr.resignation'
    _inherit = 'mail.thread'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id')
    joined_date = fields.Date(string="Join Date", required=True)
    expected_revealing_date = fields.Date(string="Revealing Date", required=True)
    resign_confirm_date = fields.Date(string="Resign confirm date")
    approved_revealing_date = fields.Date(string="Approved Date")
    reason = fields.Text(string="Reason")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('approved', 'Approved'), ('cancel', 'Cancel')],
                             string='Status', default='draft')

    @api.constrains('employee_id')
    def check_employee(self):
        for rec in self:
            if not self.env.user.has_group('hr.group_hr_user'):
                if rec.employee_id.user_id.id and rec.employee_id.user_id.id != self.env.uid:
                    raise ValidationError(_('You cannot create request for other employees'))

    @api.onchange('employee_id')
    @api.depends('employee_id')
    def check_request_existence(self):
        for rec in self:
            if rec.employee_id:
                resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
                                                                         ('state', 'in', ['confirm', 'approved'])])
                if resignation_request:
                    raise ValidationError(_('There is a resignation request in confirmed or'
                                            ' approved state for this employee'))

    @api.multi
    def _notice_period(self):
        for rec in self:
            if rec.approved_revealing_date and rec.resign_confirm_date:
                approved_date = datetime.strptime(rec.approved_revealing_date, date_format)
                confirmed_date = datetime.strptime(rec.resign_confirm_date, date_format)
                notice_period = approved_date - confirmed_date
                rec.notice_period = notice_period.days

    @api.constrains('joined_date', 'expected_revealing_date')
    def _check_dates(self):
        for rec in self:
            resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
                                                                     ('state', 'in', ['confirm', 'approved'])])
            if resignation_request:
                raise ValidationError(_('There is a resignation request in confirmed or'
                                        ' approved state for this employee'))
            if rec.joined_date >= rec.expected_revealing_date:
                raise ValidationError(_('Revealing date must be anterior to joining date'))

    @api.multi
    def confirm_resignation(self):
        for rec in self:
            rec.state = 'confirm'
            rec.resign_confirm_date = datetime.now()

    @api.multi
    def cancel_resignation(self):
        for rec in self:
            rec.state = 'cancel'

    @api.multi
    def reject_resignation(self):
        for rec in self:
            rec.state = 'rejected'

    @api.multi
    def approve_resignation(self):
        for rec in self:
            if not rec.approved_revealing_date:
                raise ValidationError(_('Enter Approved Revealing Date'))
            if rec.approved_revealing_date and rec.resign_confirm_date:
                if rec.approved_revealing_date <= rec.resign_confirm_date:
                    raise ValidationError(_('Approved revealing date must be anterior to confirmed date'))
                rec.state = 'approved'




