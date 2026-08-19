# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _


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
                                  default=lambda self: self.env.user.employee_id.id,
                                  help="Employee who is requesting the vehicle")
    req_date = fields.Date(string='Requested Date',
                           default=fields.Date.context_today, required=True,
                           help="Requested Date")
    fleet_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True,
                               help="Name of the vehicle which is requesting")
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
    is_hr = fields.Boolean(compute='_compute_is_manager', string='Is HR')
    is_manager = fields.Boolean(compute='_compute_is_manager', string='Is Manager')

    @api.model_create_multi
    def create(self, vals_list):
        """
        Generating sequence number for the employee vehicle request
        """
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('employee.fleet')
        return super(EmployeeFleet, self).create(vals_list)

    def action_send(self):
        """
        Process a vehicle request by checking availability and reserving a
        vehicle.

        This method is called when an employee requests a vehicle. It checks the
        availability of the requested vehicle by examining existing reservations
        and then either reserves the vehicle for the requested period or raises
        a UserError if it's not available.
        """
        if self.date_from and self.date_to:
            check_availability = 0
            for each in self.fleet_id.reserved_time_ids:
                if each.date_from and each.date_to:
                    # Check if date ranges overlap
                    if max(self.date_from, each.date_from) <= min(self.date_to, each.date_to):
                        check_availability = 1
                        break
                        
            if check_availability == 0:
                reserved_id = self.fleet_id.reserved_time_ids.create(
                    {'employee_id': self.employee_id.id,
                     'date_from': self.date_from,
                     'date_to': self.date_to,
                     'reserved_obj_id': self.fleet_id.id,
                     })
                self.write({'reserved_fleet_id': reserved_id.id})
                self.state = 'waiting'
            else:
                raise ValidationError(
                    _('Sorry This vehicle is already requested by another'
                      ' employee'))

    def action_approve(self):
        """
        Approve a vehicle request and notify the employee.

        This method is called when an employee's vehicle request is approved.
        It changes the state of the request to 'confirm', sends an email
        notification to the employee, and updates the mail message with the
        approval information.
        """
        if not self.is_manager:
            raise ValidationError(_("Only the HR Manager or the employee's manager can approve this request."))
        self.state = 'confirm'
        mail_content = _(
            'Hi %s,<br>Your vehicle request for the reference %s is approved.') % \
                       (self.employee_id.name, self.name)
        main_content = {
            'subject': _('%s: Approved') % self.name,
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.employee_id.work_email,
        }
        mail_id = self.env['mail.mail'].sudo().create(main_content)
        mail_id.mail_message_id.body = mail_content
        mail_id.send()
        if self.employee_id.user_id:
            mail_id.mail_message_id.write(
                {'partner_ids': [(4, self.employee_id.user_id.partner_id.id)]})
        self.fleet_id.check_availability = False

    def action_reject(self):
        """
        Reject a vehicle request and notify the employee.

        This method is called when an employee's vehicle request is rejected. It
        deletes the reservation for the request, changes the state of the
        request to 'reject', sends an email notification to the employee, and
        updates the mail message.
        """
        if not self.is_manager:
            raise ValidationError(_("Only the HR Manager or the employee's manager can reject this request."))
        self.reserved_fleet_id.sudo().unlink()
        self.state = 'reject'
        mail_content = _(
            'Hi %s,<br>Sorry, Your vehicle request for the reference %s is'
            ' Rejected.') % \
                       (self.employee_id.name, self.name)

        main_content = {
            'subject': _('%s: Rejected') % self.name,
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.employee_id.work_email,
        }
        mail_id = self.env['mail.mail'].sudo().create(main_content)
        mail_id.mail_message_id.body = mail_content
        mail_id.send()
        if self.employee_id.user_id:
            mail_id.mail_message_id.write(
                {'partner_ids': [(4, self.employee_id.user_id.partner_id.id)]})
        self.fleet_id.check_availability = True

    def action_cancel(self):
        """
        Cancel a vehicle request.

        This method is called when an employee's vehicle request is canceled. It
        checks if there is a reservation associated with the request and deletes
        it. Then, it changes the state of the request to 'cancel'.
        """
        if self.reserved_fleet_id:
            self.reserved_fleet_id.sudo().unlink()
        self.state = 'cancel'
        self.fleet_id.check_availability = True

    def action_return(self):
        """
        Mark a vehicle as returned and update its status.

        This method is called when a vehicle is returned after being used. It
        deletes the reservation associated with the request, records the return
        date and time, and updates the state of the request to 'return'.
        """
        if not self.is_manager:
            raise ValidationError(_("Only the HR Manager or the employee's manager can mark this request as returned."))
        self.reserved_fleet_id.sudo().unlink()
        self.returned_date = fields.Datetime.now()
        self.state = 'return'
        self.fleet_id.check_availability = True

    @api.onchange('date_from', 'date_to')
    def _onchange_date_from(self):
        """
        Update vehicle availability based on the selected date range.

        This onchange method is triggered when the 'date_from' or 'date_to'
        fields are changed. It iterates through the available fleet vehicles and
        checks their availability based on the selected date range. It updates
        the 'check_availability' field of each vehicle to indicate whether the
        vehicle is available during the specified period.
        """
    @api.onchange('fleet_id', 'date_from', 'date_to')
    def onchange_fleet_availability(self):
        """Check if the selected vehicle is already requested for the given dates."""
        for rec in self:
            if rec.fleet_id and rec.date_from and rec.date_to:
                for res in rec.fleet_id.reserved_time_ids:
                    if res.date_from and res.date_to:
                        if max(rec.date_from, res.date_from) <= min(rec.date_to, res.date_to):
                            raise ValidationError(_('Sorry This vehicle is already requested by another employee'))

    @api.onchange('date_from', 'date_to')
    def onchange_date_to(self):
        """Ensure that the end date is greater than the start date."""
        for each in self:
            if each.date_from and each.date_to and each.date_from > each.date_to:
                raise ValidationError(_('Date To must be greater than Date From'))

    @api.depends('employee_id')
    def _compute_is_manager(self):
        """To check the manager status"""
        for rec in self:
            rec.is_hr = self.env.user.has_group('hr.group_hr_manager') or self.env.user.has_group('hr.group_hr_user')
            rec.is_manager = rec.is_hr or (rec.employee_id.parent_id and rec.employee_id.parent_id.user_id.id == self.env.user.id)


