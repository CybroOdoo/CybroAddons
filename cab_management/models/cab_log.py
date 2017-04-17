# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import UserError


class CabLog(models.Model):
    _name = 'cab.log'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Cab'

    name = fields.Many2one('cab.management', string="Name", required=True)
    cab_log_date = fields.Date(string="Date", required=True)
    fuel_used = fields.Float(string="Fuel Used", required=True)
    seat_capacity = fields.Integer(string="Seat Capacity", related="name.seating_capacity")
    seat_available = fields.Integer(string="Seat Available")
    cab_location = fields.Many2one('cab.location', string="Location", required=True)
    seat_booked = fields.Integer(string="Seat Booked", required=True)
    odo_metre = fields.Float(string="OdoMetre Reading", required=True)
    cab_expense = fields.Float(string="Expense", required=True)
    cab_log_timing = fields.Many2one('cab.time', string="Timing", required=True)
    total_passenger = fields.Integer(string="Total Passenger", required=True)
    partner_id = fields.Many2one('res.users', string="User Name", required=True)
    cab_image = fields.Binary(string='Image', store=True, attachment=True)
    seat_check = fields.Integer(string='Seat Condition Check')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('discard', 'Discard'),
        ('cancel', 'Cancelled'),
        ('done', 'Done')
    ], default='draft')

    @api.onchange('seat_booked')
    def auto_fill_passenger_field(self):
        if self.seat_available < self.seat_booked:
            self.seat_check = 1

    @api.onchange('total_passenger')
    def error_message(self):
        if self.seat_check == 1:
            raise UserError("Sorry,No Available Seats")
        elif self.seat_booked != self.total_passenger:
            raise UserError("Sorry, No of seat requested for booking and total passenger must be equal")

    @api.one
    def action_approve(self):
        self.state = "approved"

    @api.one
    def action_cancel(self):
        self.state = "cancel"

    @api.one
    def action_discard(self):
        self.state = "discard"

    @api.onchange('cab_log_date', 'state')
    def auto_cabs_approve(self):
        for data in self.env['cab.configuration'].search([]):
            if data.auto_approve != False:
                user_obj = self.env.user
                if user_obj == data.cab_manager:
                    self.state = 'approved'

    @api.onchange('cab_log_date', 'name', 'seat_booked')
    def change_available_seat(self):
        for data in self.env['cab.management'].search([]):
            if self.name.name == data.name:
                flag = 0
                total_seat_booked = 0
                for records in self.env['cab.log'].search([]):
                    if self.cab_log_date == records.cab_log_date:
                        total_seat_booked = total_seat_booked+records.seat_booked
                        flag += 1

                if flag > 0:
                    test_val = self.seat_capacity - total_seat_booked
                    self.seat_available = test_val

                else:
                    self.seat_available = self.seat_capacity

    @api.multi
    def action_sent(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('cab_management', 'email_template_edi_cab')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        print self.ids[0]
        ctx.update({
            'default_model': 'cab.log',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        if self._context.get('default_model') == 'cab.log' and self._context.get('default_res_id'):
            order = self.env['cab.log'].browse([self._context['default_res_id']])
            if order.state == 'approved':
                order.state = 'done'
            order.sent = True
            self = self.with_context(mail_post_autofollow=True)
        return super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)
