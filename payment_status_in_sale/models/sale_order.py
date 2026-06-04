# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
###############################################################################
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    """Extend the base Sale Order model to add custom fields and behaviors
    for Sale Order Payment Status."""

    _inherit = "sale.order"
    _description = 'Sale order'

    payment_status = fields.Char(string="Payment Status",
                                 compute="_compute_payment_status",
                                 help="Field to check the payment status of the"
                                      " sale order")
    payment_details = fields.Binary(string="Payment Details",
                                    compute="_compute_payment_details",
                                    help="Shows the payment done details "
                                         "including date and amount")
    amount_due = fields.Float(string="Amount Due",
                              compute='_compute_invoice_state_and_amount_due',
                              help="Shows the amount that in due for the "
                                   "corresponding sale order")
    invoice_state = fields.Char(string="Invoice State",
                                compute="_compute_invoice_state_and_amount_due",
                                help="Field to check the invoice state of "
                                     "sale order")

    @api.depends(
        'invoice_ids',
        'invoice_ids.state',
        'invoice_ids.payment_state',
        'invoice_ids.amount_residual',
    )
    def _compute_payment_status(self):
        """ The function will compute the payment status of the sale order, if
        an invoice is created for the corresponding sale order. Payment status
        will be either paid, not paid, partially paid, in payment, reversed,
        or no invoice."""
        for order in self:
            # Only consider posted (validated) customer invoices
            posted_invoices = order.invoice_ids.filtered(
                lambda inv: inv.state == 'posted'
                and inv.move_type == 'out_invoice'
            )

            if not posted_invoices:
                order.payment_status = 'No invoice'
                continue

            states = set(posted_invoices.mapped('payment_state'))

            # Any single invoice partially paid → Partially Paid
            if 'partial' in states:
                order.payment_status = 'Partially Paid'

            # Mix of different terminal states across invoices → Partially Paid
            # e.g. one paid + one not_paid, one paid + one in_payment, etc.
            elif len(states) > 1:
                order.payment_status = 'Partially Paid'

            # All invoices share the same single state
            elif states == {'paid'}:
                order.payment_status = 'Paid' if order.amount_due == 0 \
                    else 'Partially Paid'
            elif states == {'not_paid'}:
                order.payment_status = 'Not Paid'
            elif states == {'in_payment'}:
                order.payment_status = 'In Payment'
            elif states == {'reversed'}:
                order.payment_status = 'Reversed'
            else:
                order.payment_status = 'No invoice'

    @api.depends(
        'invoice_ids',
        'invoice_ids.state',
        'invoice_ids.move_type',
        'invoice_ids.amount_residual',
        'invoice_ids.payment_state',
    )
    def _compute_invoice_state_and_amount_due(self):
        for rec in self:
            rec.invoice_state = 'No invoice'

            posted_invoices = rec.invoice_ids.filtered(
                lambda inv: inv.state == 'posted' and inv.move_type == 'out_invoice'
            )
            posted_refunds = rec.invoice_ids.filtered(
                lambda inv: inv.state == 'posted' and inv.move_type == 'out_refund'
            )

            if posted_invoices:
                rec.invoice_state = 'posted'

            invoice_residual = sum(posted_invoices.mapped('amount_residual'))
            refund_residual = sum(posted_refunds.mapped('amount_residual'))

            # Subtract unreconciled credit note balances from total due
            rec.amount_due = abs(invoice_residual - refund_residual)

    def action_open_business_doc(self):
        """ This method is intended to be used in the context of an
        account.move record.
        It retrieves the associated payment record and opens it in a new window.

        :return: A dictionary describing the action to be performed.
        :rtype: dict """
        name = _("Journal Entry")
        move = self.env['account.move'].browse(self.id)
        res_model = 'account.payment'
        res_id = move.payment_id.id
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': res_model,
            'res_id': res_id,
            'target': 'current',
        }

    def js_remove_outstanding_partial(self, partial_id):
        """ Called by the 'payment' widget to remove a reconciled entry to the
        present invoice.

        :param partial_id: The id of an existing partial reconciled with the
        current invoice.
        """
        self.ensure_one()
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        return partial.unlink()

    @api.depends('invoice_ids')
    def _compute_payment_details(self):
        """ Compute the payment details from invoices and added into the sale
        order form view. """
        for rec in self:
            payment = []
            rec.payment_details = False
            if rec.invoice_ids:
                for line in rec.invoice_ids:
                    if line.invoice_payments_widget:
                        for pay in line.invoice_payments_widget['content']:
                            payment.append(pay)
                for line in rec.invoice_ids:
                    if line.invoice_payments_widget:
                        payment_line = line.invoice_payments_widget
                        payment_line['content'] = payment
                        rec.payment_details = payment_line
                        break
                    rec.payment_details = False

    def action_register_payment(self):
        """ Open the account.payment.register wizard to pay the selected journal
         entries.
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
