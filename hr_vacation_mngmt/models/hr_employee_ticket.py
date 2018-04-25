# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrFlightTicket(models.Model):
    _name = 'hr.flight.ticket'

    name = fields.Char()
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    ticket_type = fields.Selection([('one', 'One Way'), ('round', 'Round Trip')], string='Ticket Type', default='round')
    depart_from = fields.Char(string='Departure', required=True)
    destination = fields.Char(string='Destination', required=True)
    date_start = fields.Date(string='Start Date', required=True)
    date_return = fields.Date(string='Return Date')
    ticket_class = fields.Selection([('economy', 'Economy'),
                                     ('premium_economy', 'Premium Economy'),
                                     ('business', 'Business'),
                                     ('first_class', 'First Class')], string='Class')
    ticket_fare = fields.Float(string='Ticket Fare')
    flight_details = fields.Text(string='Flight Details')
    return_flight_details = fields.Text(string='Return Flight Details')
    state = fields.Selection([('booked', 'Booked'), ('confirmed', 'Confirmed'), ('started', 'Started'),
                              ('completed', 'Completed'), ('canceled', 'Canceled')], string='Status', default='booked')
    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    leave_id = fields.Many2one('hr.holidays', string='Leave')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)

    @api.multi
    def name_get(self):
        res = []
        for ticket in self:
            res.append((ticket.id, _("Flight ticket for %s on %s to %s") % (
                ticket.employee_id.name, ticket.date_start, ticket.destination)))
        return res

    @api.constrains('date_start', 'date_return')
    def check_valid_date(self):
        if self.filtered(lambda c: c.date_return and c.date_start > c.date_return):
            raise ValidationError(_('Flight travelling start date must be less than flight return date.'))

    def book_ticket(self):
        return {'type': 'ir.actions.act_window_close'}

    def confirm_ticket(self):
        if self.ticket_fare <= 0:
            raise UserError(_('Please add ticket fare.'))
        inv_obj = self.env['account.invoice'].sudo()
        expense_account = self.env['ir.config_parameter'].sudo().get_param('travel_expense_account')
        if not expense_account:
            raise UserError(_('Please select expense account for the flight tickets.'))
        domain = [
            ('type', '=', 'purchase'),
            ('company_id', '=', self.company_id.id),
        ]
        journal_id = self.env['account.journal'].search(domain, limit=1)
        partner = self.env.ref('hr_vacation_mngmt.air_lines_partner')
        if not partner.property_payment_term_id:
            date_due = fields.Date.context_today(self)
        else:
            pterm = partner.property_payment_term_id
            pterm_list = \
                pterm.with_context(currency_id=self.env.user.company_id.id).compute(
                    value=1, date_ref=fields.Date.context_today(self))[0]
            date_due = max(line[0] for line in pterm_list)
        inv_data = {
            'name': '',
            'origin': 'Flight Ticket',
            'type': 'in_invoice',
            'journal_id': journal_id.id,
            'payment_term_id': partner.property_payment_term_id.id,
            'date_due': date_due,
            'reference': False,
            'partner_id': partner.id,
            'account_id': partner.property_account_payable_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Flight Ticket',
                'price_unit': self.ticket_fare,
                'quantity': 1.0,
                'account_id': expense_account,
            })],
        }
        inv_id = inv_obj.create(inv_data)
        inv_id.action_invoice_open()
        self.write({'state': 'confirmed', 'invoice_id': inv_id.id})

    def cancel_ticket(self):
        if self.state == 'booked':
            self.write({'state': 'canceled'})
        elif self.state == 'confirmed':
            if self.invoice_id and self.invoice_id.state == 'paid':
                self.write({'state': 'canceled'})
            if self.invoice_id and self.invoice_id.state == 'open':
                self.invoice_id.action_invoice_cancel()
                self.write({'state': 'canceled'})

    @api.model
    def run_update_ticket_status(self):
        run_out_tickets = self.search([('state', 'in', ['confirmed', 'started']),
                                       ('date_return', '<=', datetime.now())])
        confirmed_tickets = self.search([('state', '=', 'confirmed'), ('date_start', '<=', datetime.now()),
                                         ('date_return', '>', datetime.now())])
        for ticket in run_out_tickets:
            ticket.write({'state': 'completed'})
        for ticket in confirmed_tickets:
            ticket.write({'state': 'started'})

    @api.multi
    def action_view_invoice(self):
        return {
            'name': _('Flight Ticket Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.invoice_supplier_form').id,
            'res_model': 'account.invoice',
            'context': "{'type':'in_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_id.id,
        }
