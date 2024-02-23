# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright(C) 2023-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Shyamgeeth P.P (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
import json
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    """Sale order model inherited for adding status of payment of sales."""
    _inherit = "sale.order"

    payment_status = fields.Char(string="Payment Status",
                                 compute="_compute_payment_status",
                                 help="Field to check the payment status of the"
                                      " sale order")
    payment_details = fields.Text(string="Payment Details",
                                  compute="_compute_payment_details",
                                  help="Shows the payment done details"
                                       " including date and amount")
    amount_due = fields.Float(string="Amount Due",
                              compute='_compute_amount_due',
                              help="Shows the amount that in due for the "
                                   "corresponding sale order")
    invoice_state = fields.Char(string="Invoice State",
                                compute="_compute_invoice_state",
                                help="Field to check the invoice state of "
                                     "sale order")

    @api.depends('invoice_ids')
    def _compute_payment_status(self):
        """ The function will compute the payment status of the sale order,
        if an invoice is created for the corresponding sale order.Payment
        status will be either in paid,not paid,partially paid, reversed etc."""
        for order in self:
            order.payment_status = 'No invoice'
            payment_states = order.invoice_ids. \
                filtered(lambda i: i.state == 'posted').mapped('payment_state')
            status_length = len(payment_states)
            if status_length != 0:
                if 'partial' in payment_states:
                    order.payment_status = 'Partially Paid'
                elif 'not_paid' in payment_states and status_length == 1:
                    order.payment_status = 'Not Paid'
                elif 'not_paid' in payment_states and order.amount_due != \
                        order.amount_total and status_length > 1:
                    order.payment_status = 'Partially Paid'
                elif 'paid' in payment_states and status_length == \
                        payment_states.count('paid') and order.amount_due == 0:
                    order.payment_status = 'Paid'
                elif 'paid' in payment_states and status_length == \
                        payment_states.count('paid') and order.amount_due != 0:
                    order.payment_status = 'Partially Paid'
                elif 'in_payment' in payment_states and \
                        status_length == payment_states.count('in_payment'):
                    order.payment_status = 'In Payment'
                elif 'reversed' in payment_states and \
                        status_length == payment_states.count('reversed'):
                    order.payment_status = 'Reversed'
                else:
                    order.payment_status = 'No invoice'

    @api.depends('invoice_ids')
    def _compute_invoice_state(self):
        """The function will compute the state of the invoice ,
        Once an invoice is existing in a sale order."""
        for rec in self:
            rec.invoice_state = 'No invoice'
            for order in rec.invoice_ids:
                if order.state == 'posted':
                    rec.invoice_state = 'posted'
                elif order.state != 'posted':
                    rec.invoice_state = 'draft'
                else:
                    rec.invoice_state = 'No invoice'

    @api.depends('invoice_ids')
    def _compute_amount_due(self):
        """The function is used to compute the amount due from the invoice and
         if payment is registered."""
        for rec in self:
            amount_due = 0
            for order in rec.invoice_ids:
                amount_due = amount_due + order.amount_residual
            rec.amount_due = amount_due

    @api.depends('invoice_ids')
    def _compute_payment_details(self):
        """Compute the payment details from invoices and added into the
        sale order form view."""
        for rec in self:
            payment = []
            rec.payment_details = False
            for order in rec.invoice_ids:
                if order.invoice_payments_widget != 'false':
                    for pay in json.loads(order.invoice_payments_widget)[
                        'content']:
                        payment.append(pay)
            for order in rec.invoice_ids:
                if order.invoice_payments_widget != 'false':
                    payment_line = json.loads(order.invoice_payments_widget)
                    payment_line['content'] = payment
                    rec.payment_details = json.dumps(payment_line)
                    break

    def action_register_payment(self):
        """ Open the account.payment.register wizard to pay the selected
        journal entries.
        :return: An action opening the account.payment.register wizard.
        """
        self.ensure_one()
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.invoice_ids.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
