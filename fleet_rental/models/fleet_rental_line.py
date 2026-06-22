# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
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
from odoo import fields, models


class FleetRentalLine(models.Model):
    """
    Model for tracking recurring invoices and payment stages for fleet rentals.
    """
    _name = 'fleet.rental.line'
    _description = "More details for fleet rental"

    name = fields.Char(string='Description', help='Name')
    date_today = fields.Date(string='Date', help='Today date')
    account_info = fields.Char(string='Account', help='Info of the account')
    recurring_amount = fields.Float(string='Amount',
                                    help='Amount of the recurring invoice')
    rental_number = fields.Many2one('car.rental.contract',
                                    string='Rental Number',
                                    help='Reference of the rental')
    payment_info = fields.Char(compute='_compute_payment_info',
                               string='Payment Stage',
                               default='draft', help='Info of the payment')
    invoice_number = fields.Integer(string='Invoice ID',
                                    help='ID of the invoice')
    invoice_ref = fields.Many2one('account.move',
                                  string='Invoice Ref',
                                  help='Reference of the invoice')
    date_due = fields.Date(string='Due Date',
                           help='Due date ',
                           related='invoice_ref.invoice_date_due')

    def _compute_payment_info(self):
        """
            Retrieve payment information for the current record.
            Check the state of the associated invoice based on the provided
            invoice reference.
            If the record exists, set the payment_info field to the state of
            the invoice.
            Otherwise, set the payment_info field to 'Record Deleted'.
        """
        for record in self:
            invoice = record.invoice_ref
            if invoice.exists():
                record.payment_info = invoice.payment_state or invoice.state
            else:
                record.payment_info = 'Record Deleted'
