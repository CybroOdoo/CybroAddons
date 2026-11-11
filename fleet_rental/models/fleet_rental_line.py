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
from odoo import api, fields, models


class FleetRentalLine(models.Model):
    _name = 'fleet.rental.line'
    _description = "More details for fleet rental"

    name = fields.Char(string='Description', help='Name')
    date_today = fields.Date(string='Date', help='Today date')
    account_info = fields.Char(string='Account', help='Info of the account')
    recurring_amount = fields.Float(
        help='Amount of the recurring invoice',
    )
    rental_number = fields.Many2one(
        comodel_name='car.rental.contract',
        help='Reference of the rental',
    )
    payment_info = fields.Char(
        compute='_compute_payment_info',
        string='Payment Stage',
        default='draft',
        help='Info of the payment',
    )
    invoice_number = fields.Integer(
        string='Invoice ID',
        help='ID of the invoice',
    )
    invoice_ref = fields.Many2one(
        comodel_name='account.move',
        help='Reference of the invoice',
    )
    date_due = fields.Date(
        string='Due Date',
        help='Due date ',
        related='invoice_ref.invoice_date_due',
    )

    @api.depends('invoice_ref.payment_state', 'invoice_ref.state', 'invoice_number')
    def _compute_payment_info(self):
        """
            Retrieve payment information for the current record.
            Check the payment_state and state of the associated invoice based on
            the provided invoice reference or number.
            If the record exists, set the payment_info field to the payment_state
            if paid/in_payment, otherwise the state of the invoice.
            Otherwise, set the payment_info field to 'Record Deleted'.
        """
        for each in self:
            invoice = each.invoice_ref
            if not invoice and each.invoice_number:
                invoice = self.env['account.move'].browse(each.invoice_number).exists()
            if invoice:
                if invoice.payment_state in ('paid', 'in_payment', 'reversed'):
                    each.payment_info = invoice.payment_state
                elif invoice.state:
                    each.payment_info = invoice.state
                else:
                    each.payment_info = invoice.payment_state or 'draft'
            else:
                each.payment_info = 'Record Deleted'
