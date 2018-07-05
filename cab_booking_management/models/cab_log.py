# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class CabLog(models.Model):
    _name = 'cab.log'
    _inherit = 'mail.thread'
    _description = 'Cab'

    name = fields.Many2one('cab.management', string="Name", store=True, required=True)
    cab_log_date = fields.Date(string="Date", default=date.today(), required=True)
    fuel_used = fields.Float(string="Fuel Used", required=True, help="To get total fuel used in Litre")
    seat_capacity = fields.Integer(string="Seat Capacity", related="name.seating_capacity")
    seat_available = fields.Integer(string="Seat Available")
    cab_location = fields.Char(string="Destination Point", required=True)
    cab_location_from = fields.Char(string="Starting Point", required=True)
    seat_booked = fields.Integer(string="How many seats you need to book?", required=True)
    odo_metre = fields.Float(string="OdoMetre Reading", required=True, help="Total distance covered in Km")
    cab_expense = fields.Float(string="Expense", required=True)
    cab_log_timing = fields.Many2one('cab.time', string="Time", required=True)
    total_passenger = fields.Integer(string="Total Passenger", required=True)
    partner_id = fields.Many2one('res.users', string="Customer Name", required=True)
    cab_image = fields.Binary(string='Image', store=True, attachment=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('discard', 'Discard'),
        ('cancel', 'Cancelled'),
        ('done', 'Done')
    ], default='draft')

    @api.onchange('name')
    def change_location(self):
        for records in self.env['cab.timing'].search([('name.name', '=', self.name.name)]):
            if self.name.name == records.name.name:
                self.cab_location = records.cab_route_to.name
                self.cab_location_from = records.cab_route.name

    @api.one
    @api.constrains('cab_log_timing')
    def change_time(self):
        for records in self.env['cab.timing'].search([('name.name', '=', self.name.name)]):
            if self.cab_log_timing:
                if self.cab_log_timing not in records.cab_time:
                    raise ValidationError("No cabs available at given time")

    @api.one
    @api.constrains('seat_booked')
    def error_message(self):
        if self.seat_available < self.seat_booked:
            raise ValidationError("No Available Seats")
        elif self.seat_booked != self.total_passenger:
            raise ValidationError("No of seat requested for booking and total passenger must be equal")

    @api.onchange('seat_booked')
    def change_total_passenger(self):
        self.total_passenger = self.seat_booked

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

    @api.onchange('cab_log_date', 'name', 'cab_log_timing')
    def change_available_seat(self):
        for data in self.env['cab.management'].search([('name', '=', self.name.name)]):
            flag = 0
            total_seat_booked = 0
            for records in self.env['cab.log'].search([('name.name', '=', data.name)]):
                if self.cab_log_date == records.cab_log_date and self.cab_log_timing == records.cab_log_timing:
                    if self.cab_location == records.cab_location and self.cab_location_from == records.cab_location_from:
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
            template_id = ir_model_data.get_object_reference('cab_booking_management', 'email_template_edi_cab')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
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
