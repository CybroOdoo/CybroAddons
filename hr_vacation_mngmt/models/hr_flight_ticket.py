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
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrFlightTicket(models.Model):
    """Model representing flight tickets for employees."""
    _name = 'hr.flight.ticket'
    _description = 'HR Flight Ticket'

    name = fields.Char(string='Sequence No', readonly=True,
                       default=lambda self: _('New'),
                       copy=False,
                       help="Sequence number of Flight Ticket")
    employee_id = fields.Many2one('hr.leave', string='Employee',
                                  required=True, help="Name of the employee")
    ticket_type = fields.Selection(
        [('one', 'One Way'), ('round', 'Round Trip')],
        string='Ticket Type', default='round', help="Select the ticket type")
    depart_from = fields.Char(string='Departure', required=True,
                              help="Specify the departure place.")
    destination = fields.Char(string='Destination', required=True,
                              help="Specify the destination place.")
    date_start = fields.Date(string='Start Date', required=True,
                             help="Start date of the travel.")
    date_return = fields.Date(string='Return Date', help="Return date ")
    ticket_class = fields.Selection([('economy', 'Economy'),
                                     ('premium_economy', 'Premium Economy'),
                                     ('business', 'Business'),
                                     ('first_class', 'First Class')],
                                    string='Class',
                                    help="Select the ticket class")
    ticket_fare = fields.Float(string='Ticket Fare',
                               help="Give the ticket fare")
    flight_details = fields.Text(string='Flight Details',
                                 help="Flight details of the employee.")
    return_flight_details = fields.Text(string='Return Flight Details',
                                        help="Details of return flight ")
    state = fields.Selection([('booked', 'Booked'),
                              ('confirmed', 'Confirmed'),
                              ('started', 'Started'),
                              ('completed', 'Completed'),
                              ('canceled', 'Canceled')], string='Status',
                             default='booked',
                             help='States of the flight ticket. ')
    invoice_id = fields.Many2one('account.move', string='Invoice',
                                 help="Invoice of the employee")
    leave_id = fields.Many2one('hr.leave', string='Leave',
                               help="Leave of the employee.")
    company_id = fields.Many2one('res.company', 'Company',
                                 help="Company of the employee.",
                                 default=lambda self: self.env.user.company_id)

    @api.model
    def create(self, vals):
        """Function declared for creating sequence Number for Flight Ticket"""
        vals=vals[0] if isinstance(vals,list) else vals
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'hr.flight.ticket') or _('New')
        res = super(HrFlightTicket, self).create(vals)
        return res

    @api.constrains('date_start', 'date_return')
    def check_valid_date(self):
        """Constraint method 'check_valid_date' for the model, validating
         the consistency of flight ticket dates."""
        if self.filtered(
                lambda c: c.date_return and c.date_start > c.date_return):
            raise ValidationError(
                _('Flight travelling start date must be less than flight'
                  ' return date.'))

    def action_confirm_ticket(self):
        """This method confirms the flight ticket and generates an
         invoice for the ticket fare."""
        product_id = self.env['product.product'].search(
            [("name", "=", "Flight Ticket")])
        if self.ticket_fare <= 0:
            raise UserError(_('Please add ticket fare.'))
        expense_account = self.env['ir.config_parameter'].sudo().get_param(
            'hr_vacation_mngmt.expense_id')
        if not expense_account:
            raise UserError(
                _('Please select expense account for the flight tickets.'))
        journal_id = self.env['account.journal'].search(
            [('type', '=', 'purchase'),
             ('company_id', '=', self.company_id.id)], limit=1)
        partner = self.env.ref('hr_vacation_mngmt.res_partner_data_airlines')
        if not partner.property_payment_term_id:
            date_due = fields.Date.context_today(self)
        else:
            pterm = partner.property_payment_term_id
            pterm_list = \
                pterm.with_context(
                    currency_id=self.env.user.company_id.id).compute(
                    value=1, date_ref=fields.Date.context_today(self))[0]
            date_due = max(line[0] for line in pterm_list)
        inv_id = self.env['account.move'].create([{
            'name': '/',
            'invoice_origin': 'Flight Ticket',
            'move_type': 'in_invoice',
            'journal_id': journal_id.id,
            'invoice_date_due': date_due,
            'ref': False,
            'partner_id': partner.id,
            'state': 'draft',
            'invoice_line_ids': [(0, 0, {
                'name': 'Flight Ticket',
                'price_unit': self.ticket_fare,
                'quantity': 1.0,
                'account_id': int(expense_account),
                'product_id': product_id.id,
            })],
        }])
        self.write({'state': 'confirmed', 'invoice_id': inv_id.id})

    def action_cancel_ticket(self):
        """This method cancels the flight ticket,
        updating its state to 'canceled'. If the ticket is in the 'booked'
        state, it is directly marked as 'canceled'.If the ticket is in the
        'confirmed' state, it checks the associated invoice's state"""
        if self.state == 'booked':
            self.write({'state': 'canceled'})
        elif self.state == 'confirmed':
            if self.invoice_id and self.invoice_id.state == 'draft':
                self.write({'state': 'canceled'})
            if self.invoice_id and self.invoice_id.state == 'open':
                self.invoice_id.action_invoice_cancel()
                self.write({'state': 'canceled'})

    @api.model
    def run_update_ticket_status(self):
        """This model method is designed to be scheduled and automatically
         updates the state of flight tickets based on their current status
         and relevant date conditions."""
        run_out_tickets = self.search(
            [('state', 'in', ['confirmed', 'started']),
             ('date_return', '<=', datetime.now())])
        confirmed_tickets = self.search(
            [('state', '=', 'confirmed'), ('date_start', '<=', datetime.now()),
             ('date_return', '>', datetime.now())])
        for ticket in run_out_tickets:
            ticket.write({'state': 'completed'})
        for ticket in confirmed_tickets:
            ticket.write({'state': 'started'})

    def action_view_invoice(self):
        """This method opens the view for the associated invoice of the
         flight ticket."""
        return {
            'name': _('Flight Ticket Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'type':'in_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_id.id,
        }

    def action_book_ticket(self):
        """It returns an action to close the current window."""
        return {
            'type': 'ir.actions.act_window_close'
        }
