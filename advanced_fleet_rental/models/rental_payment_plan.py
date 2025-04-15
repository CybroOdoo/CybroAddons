# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from datetime import date
from odoo import api, fields, models


class RentalPaymentPlan(models.Model):
    """
    Model for managing rental payment plans associated with fleet rental
    contracts.
    """
    _name = 'rental.payment.plan'
    _description = 'Rental Payment Plan'

    contract_id = fields.Many2one(
        'fleet.rental.contract', string='Rental Contract',
        ondelete='cascade')
    invoice_item_id = fields.Many2one('product.product',
                                   string='Invoice Item', )
    payment_date = fields.Date(string='Payment Date' )
    payment_amount = fields.Float(
        string='Payment Amount',
        help='Amount to be paid based on the invoice item.')
    invoice_id = fields.Many2one('account.move', string='Invoice',
                                 readonly=True)
    payment_state = fields.Selection(
        [
            ('not_paid', 'Not Paid'),
            ('in_payment', 'In Payment'),
            ('paid', 'Paid'),
            ('partial', 'Partially Paid'),
            ('reversed', 'Reversed'),
            ('invoicing_legacy', 'Invoicing App Legacy'),
        ], compute='_compute_payment_state',
        string='Payment State')
    is_invoiced = fields.Boolean(string="Invoice Button", help="Invoiced")

    @api.depends('invoice_id.payment_state')
    def _compute_payment_state(self):
        """
        Computes the payment state based on the associated invoice's
        payment state.
        """
        for record in self:
            if record.invoice_id:
                record.payment_state = record.invoice_id.payment_state
            else:
                record.payment_state = 'not_paid'

    def action_create_invoice(self):
        """
        Creates an invoice for the payment plan.
        """
        self.ensure_one()
        invoice_vals = {
            'partner_id': self.contract_id.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': self.payment_date,
            'vehicle_rental_id': self.contract_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.invoice_item_id.id,
                'name': self.invoice_item_id.name,
                'quantity': 1,
                'price_unit': self.payment_amount,
            })],
        }
        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()
        self.invoice_id = invoice.id
        self.is_invoiced = True
        return invoice

    @api.model
    def _schedule_auto_invoice_checker(self):
        """
        Scheduled action to automatically generate invoices for rental payment
        plans where the payment date is today. Searches for payment plans with
        today's date and no associated invoice, and generates invoices for them.
        """
        today = date.today()
        payment_plans = self.search([
            ('payment_date', '=', today),
            ('invoice_id', '=', False)
        ])
        for plan in payment_plans:
            plan.action_create_invoice()
