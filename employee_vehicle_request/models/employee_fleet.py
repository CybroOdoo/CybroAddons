# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nilmar Shereef @ Cybrosys, (odoo@cybrosys.com)
#            Niyas Raphy @ Cybrosys, (odoo@cybrosys.com)
#            Yadhukrishna @ Cybrosys, (odoo@cybrosys.com)
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
#############################################################################
# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FleetReservedTime(models.Model):
    _name = "fleet.reserved"
    _description = "Reserved Time"

    employee = fields.Many2one('hr.employee', string='Employee')
    date_from = fields.Datetime(string='Reserved Date From')
    date_to = fields.Datetime(string='Reserved Date To')
    reserved_obj = fields.Many2one('fleet.vehicle')


class FleetVehicleInherit(models.Model):
    _inherit = 'fleet.vehicle'

    check_availability = fields.Boolean(default=True, copy=False)
    reserved_time = fields.One2many('fleet.reserved', 'reserved_obj', String='Reserved Time', readonly=1,
                                    ondelete='cascade')


class EmployeeFleet(models.Model):
    _name = 'employee.fleet'
    _description = 'Employee Vehicle Request'
    _inherit = 'mail.thread'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('employee.fleet')
        return super(EmployeeFleet, self).create(vals)

    def send(self):
        if self.date_from and self.date_to:
            fleet_obj = self.env['fleet.vehicle'].search([])
            check_availability = 0
            for i in fleet_obj:
                for each in i.reserved_time:
                    if each.date_from and each.date_to:
                        if each.date_from <= self.date_from <= each.date_to:
                            check_availability = 1
                        elif self.date_from < each.date_from:
                            if each.date_from <= self.date_to <= each.date_to:
                                check_availability = 1
                            elif self.date_to > each.date_to:
                                check_availability = 1
                            else:
                                check_availability = 0
                        else:
                            check_availability = 0
            if check_availability == 0:
                reserved_id = self.fleet.reserved_time.create({'employee': self.employee.id,
                                                               'date_from': self.date_from,
                                                               'date_to': self.date_to,
                                                               'reserved_obj': self.fleet.id,
                                                               })
                self.write({'reserved_fleet_id': reserved_id.id})
                self.state = 'waiting'
            else:
                raise UserError(_('Sorry This vehicle is already requested by another employee'))

    def approve(self):
        # self.fleet.fleet_status = True
        self.state = 'confirm'
        mail_content = _('Hi %s,<br>Your vehicle request for the reference %s is approved.') % \
                        (self.employee.name, self.name)
        main_content = {
            'subject': _('%s: Approved') % self.name,
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.employee.work_email,
        }
        mail_id = self.env['mail.mail'].create(main_content)
        mail_id.mail_message_id.body = mail_content
        mail_id.send()
        if self.employee.user_id:
            # mail_id.mail_message_id.write({'notified_partner_ids': [(4, self.employee.user_id.partner_id.id)]})
            mail_id.mail_message_id.write({'partner_ids': [(4, self.employee.user_id.partner_id.id)]})

    def reject(self):
        self.reserved_fleet_id.unlink()
        self.state = 'reject'
        mail_content = _('Hi %s,<br>Sorry, Your vehicle request for the reference %s is Rejected.') % \
                        (self.employee.name, self.name)

        main_content = {
            'subject': _('%s: Approved') % self.name,
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': self.employee.work_email,
        }
        mail_id = self.env['mail.mail'].create(main_content)
        mail_id.mail_message_id.body = mail_content
        mail_id.send()
        if self.employee.user_id:
            # mail_id.mail_message_id.write({'notified_partner_ids': [(4, self.employee.user_id.partner_id.id)]})
            mail_id.mail_message_id.write({'partner_ids': [(4, self.employee.user_id.partner_id.id)]})

    def cancel(self):
        if self.reserved_fleet_id:
            self.reserved_fleet_id.unlink()
        self.state = 'cancel'

    def returned(self):
        self.reserved_fleet_id.unlink()
        self.returned_date = fields.datetime.now()
        self.state = 'return'

    @api.constrains('date_from', 'date_to')
    def onchange_date_to(self):
        for each in self:
            if each.date_from > each.date_to:
                raise UserError(_('Date To must be greater than Date From'))

    @api.onchange('date_from', 'date_to')
    def check_availability(self):
        if self.date_from and self.date_to:
            self.fleet = ''
            fleet_obj = self.env['fleet.vehicle'].search([])
            for i in fleet_obj:
                for each in i.reserved_time:
                    if each.date_from and each.date_to:
                        if each.date_from <= self.date_from <= each.date_to:
                            i.write({'check_availability': False})
                        elif self.date_from < each.date_from:
                            if each.date_from <= self.date_to <= each.date_to:
                                i.write({'check_availability': False})
                            elif self.date_to > each.date_to:
                                i.write({'check_availability': False})
                            else:
                                i.write({'check_availability': True})
                        else:
                            i.write({'check_availability': True})

    reserved_fleet_id = fields.Many2one('fleet.reserved', invisible=1, copy=False)
    name = fields.Char(string='Request Number', copy=False)
    employee = fields.Many2one('hr.employee', string='Employee', required=1, readonly=True,
                               states={'draft': [('readonly', False)]})
    req_date = fields.Date(string='Requested Date', default=fields.Date.context_today, required=1, readonly=True,
                           states={'draft': [('readonly', False)]}, help="Requested Date")
    fleet = fields.Many2one('fleet.vehicle', string='Vehicle', required=1, readonly=True,
                            states={'draft': [('readonly', False)]})
    date_from = fields.Datetime(string='From', required=1, readonly=True,
                                states={'draft': [('readonly', False)]})
    date_to = fields.Datetime(string='To', required=1, readonly=True,
                              states={'draft': [('readonly', False)]})
    returned_date = fields.Datetime(string='Returned Date', readonly=1)
    purpose = fields.Text(string='Purpose', required=1, readonly=True,
                          states={'draft': [('readonly', False)]}, help="Purpose")
    state = fields.Selection([('draft', 'Draft'), ('waiting', 'Waiting for Approval'), ('cancel', 'Cancel'),
                              ('confirm', 'Approved'), ('reject', 'Rejected'), ('return', 'Returned')],
                             string="State", default="draft")

