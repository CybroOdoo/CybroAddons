# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import api, Command, fields, models, _


class EmployeeFleet(models.Model):
    """
    Manage employee vehicle requests, including reservation handling, availability
    checks, approval workflow, and lifecycle states such as draft, approval,
    rejection, cancellation, and return.
    """
    _name = 'employee.fleet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Vehicle Request'

    reserved_fleet_id = fields.Many2one('fleet.reserved',
                                        copy=False, help="Reserved fleet")
    name = fields.Char(string='Request Number', copy=False,
                       help="Sequence number of the vehicle request")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  help="Employee who is requesting the vehicle")
    req_date = fields.Date(string='Requested Date',
                           default=fields.Date.context_today, required=True,
                           help="Requested Date")
    fleet_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True,
                               domain="[('id', 'in', available_fleet_ids)]",
                               help="Vehicle requested by the employee")
    available_fleet_ids = fields.Many2many(
        'fleet.vehicle',
        compute='_compute_available_fleet_ids',
        help='Technical field to compute available vehicles for the requested period',
    )
    date_from = fields.Datetime(string='From date', required=True,
                                help='Date from which employee needs the vehicle')
    date_to = fields.Datetime(string='To date', required=True,
                              help='Date till employee needs the vehicle')
    returned_date = fields.Datetime(string='Returned Date', readonly=True,
                                    help='Returned date of the vehicle')
    purpose = fields.Text(string='Purpose', required=True,
                          help="Purpose for the vehicle request")
    state = fields.Selection(
        [('draft', 'Draft'), ('waiting', 'Waiting for Approval'),
         ('cancel', 'Cancel'), ('confirm', 'Approved'), ('reject', 'Rejected'),
         ('return', 'Returned')],
        string="State", default="draft", help="State of the vehicle request")

    @api.depends('date_from', 'date_to', 'reserved_fleet_id')
    def _compute_available_fleet_ids(self):
        """
        Compute vehicles that do not have overlapping reservations for the
        requested period.
        """
        for rec in self:
            if rec.date_from and rec.date_to:
                overlapping = self.env['fleet.reserved'].sudo().search([
                    ('date_from', '<=', rec.date_to),
                    ('date_to', '>=', rec.date_from),
                ])
                if rec.reserved_fleet_id:
                    overlapping = overlapping - rec.reserved_fleet_id
                reserved_vehicle_ids = overlapping.mapped('reserved_obj_id').ids
                rec.available_fleet_ids = self.env['fleet.vehicle'].search([
                    ('id', 'not in', reserved_vehicle_ids)
                ])
            else:
                rec.available_fleet_ids = self.env['fleet.vehicle'].search([])

    @api.model_create_multi
    def create(self, vals_list):
        """
        Generating sequence number for the employee vehicle request
        """
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('employee.fleet')
        return super().create(vals_list)

    def action_send(self):
        """
        Process a vehicle request by checking availability and reserving a
        vehicle.
        """
        for rec in self:
            if rec.date_from and rec.date_to:
                overlapping = self.env['fleet.reserved'].sudo().search([
                    ('reserved_obj_id', '=', rec.fleet_id.id),
                    ('date_from', '<=', rec.date_to),
                    ('date_to', '>=', rec.date_from),
                ])
                if rec.reserved_fleet_id:
                    overlapping = overlapping - rec.reserved_fleet_id
                if overlapping:
                    raise UserError(
                        _('Sorry, this vehicle is already requested by another'
                          ' employee.'))
                reserved_id = self.env['fleet.reserved'].create({
                    'employee_id': rec.employee_id.id,
                    'date_from': rec.date_from,
                    'date_to': rec.date_to,
                    'reserved_obj_id': rec.fleet_id.id,
                })
                rec.write({
                    'reserved_fleet_id': reserved_id.id,
                    'state': 'waiting',
                })

    def _check_approval_rights(self):
        """
        Verify that the current user belongs to HR Officer or HR Manager group.
        """
        if not (self.env.user.has_group('hr.group_hr_user') or
                self.env.user.has_group('hr.group_hr_manager')):
            raise AccessError(
                _('Only HR Officers or Managers can perform this action.'))

    def action_approve(self):
        """
        Approve a vehicle request and notify the employee.
        """
        self._check_approval_rights()
        for rec in self:
            rec.state = 'confirm'
            mail_content = _(
                'Hi %(name)s,<br>Your vehicle request for the reference %(reference)s is approved.',
                name=rec.employee_id.name,
                reference=rec.name,
            )
            main_content = {
                'subject': _('%(reference)s: Approved', reference=rec.name),
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': rec.employee_id.work_email,
            }
            mail_id = self.env['mail.mail'].sudo().create(main_content)
            mail_id.mail_message_id.body = mail_content
            mail_id.send()
            if rec.employee_id.user_id:
                mail_id.mail_message_id.write(
                    {'partner_ids': [Command.link(rec.employee_id.user_id.partner_id.id)]})

    def action_reject(self):
        """
        Reject a vehicle request and notify the employee.
        """
        self._check_approval_rights()
        for rec in self:
            if rec.reserved_fleet_id:
                rec.reserved_fleet_id.unlink()
            rec.state = 'reject'
            mail_content = _(
                'Hi %(name)s,<br>Sorry, your vehicle request for the reference %(reference)s is'
                ' rejected.',
                name=rec.employee_id.name,
                reference=rec.name,
            )

            main_content = {
                'subject': _('%(reference)s: Rejected', reference=rec.name),
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': rec.employee_id.work_email,
            }
            mail_id = self.env['mail.mail'].sudo().create(main_content)
            mail_id.mail_message_id.body = mail_content
            mail_id.send()
            if rec.employee_id.user_id:
                mail_id.mail_message_id.write(
                    {'partner_ids': [Command.link(rec.employee_id.user_id.partner_id.id)]})

    def action_cancel(self):
        """
        Cancel a vehicle request.
        """
        for rec in self:
            if rec.reserved_fleet_id:
                rec.reserved_fleet_id.unlink()
            rec.state = 'cancel'

    def action_return(self):
        """
        Mark a vehicle as returned and update its status.
        """
        self._check_approval_rights()
        for rec in self:
            if rec.reserved_fleet_id:
                rec.reserved_fleet_id.unlink()
            rec.returned_date = fields.Datetime.now()
            rec.state = 'return'

    @api.onchange('date_from', 'date_to')
    def _onchange_date_from(self):
        """
        Reset selected vehicle if it is no longer available in the newly selected
        date range.
        """
        if self.date_from and self.date_to and self.fleet_id:
            if self.fleet_id not in self.available_fleet_ids:
                self.fleet_id = False

    @api.constrains('date_from', 'date_to')
    def _check_date_to(self):
        """Ensure that the end date is greater than the start date."""
        for each in self:
            if each.date_from and each.date_to and each.date_from > each.date_to:
                raise ValidationError(_('Date To must be greater than Date From'))



