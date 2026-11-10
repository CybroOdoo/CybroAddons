# -*- coding: utf-8 -*-
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
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    """ Extend the base Sale Order model to add custom fields and behaviors
    for Sale Order Payment Status. """
    _inherit = "sale.order"
    _description = 'Sale order'

    payment_status = fields.Char(compute="_compute_payment_status",
                                 help="Field to check the payment status of the"
                                      " sale order")
    payment_details = fields.Json(compute="_compute_payment_details",
                                  help="Shows the payment done details "
                                       "including date and amount")
    amount_due = fields.Float(compute='_compute_amount_due',
                              help="Shows the amount that is due for the "
                                   "corresponding sale order")
    invoice_state = fields.Char(compute="_compute_invoice_state",
                                help="Field to check the invoice state of "
                                     "sale order")

    @api.depends('invoice_ids.state', 'invoice_ids.payment_state', 'amount_due')
    def _compute_payment_status(self):
        """ The function will compute the payment status of the sale order, if
        an invoice is created for the corresponding sale order.Payment status
        will be either in paid,not paid,partially paid, reversed etc. """
        for order in self:
            order.payment_status = 'No invoice'
            posted_invoices = order.invoice_ids.filtered(
                lambda x: x.state == 'posted')
            if not posted_invoices:
                order.payment_status = 'No invoice'
            else:
                payment_states = posted_invoices.mapped('payment_state')
                status_length = len(payment_states)
                if order.amount_due > 0:
                    if 'not_paid' in payment_states and status_length == payment_states.count('not_paid'):
                        order.payment_status = 'Not Paid'
                    elif 'partial' in payment_states or 'not_paid' in payment_states:
                        order.payment_status = 'Partially Paid'
                elif order.amount_due <= 0:  # Changed to <= 0 to handle overpayments or credit notes
                    if 'paid' in payment_states and status_length == payment_states.count(
                            'paid'):
                        order.payment_status = 'Paid'
                    elif 'in_payment' in payment_states and status_length == payment_states.count(
                            'in_payment'):
                        order.payment_status = 'In Payment'
                elif 'reversed' in payment_states and status_length == payment_states.count(
                        'reversed'):
                    order.payment_status = 'Reversed'

    @api.depends('invoice_ids.state')
    def _compute_invoice_state(self):
        """ The function will compute the state of the invoice , Once an invoice
        is existing in a sale order. """
        for rec in self:
            rec.invoice_state = 'No invoice'
            for order in rec.invoice_ids:
                if order.state == 'posted':
                    rec.invoice_state = 'posted'
                elif order.state != 'posted':
                    rec.invoice_state = 'draft'
                else:
                    rec.invoice_state = 'No invoice'

    @api.depends('invoice_ids.state', 'invoice_ids.amount_total', 'invoice_ids.amount_residual')
    def _compute_amount_due(self):
        """The function is used to compute the amount due from the invoice and
        if payment is registered, accounting for exchange rate differences and credit notes."""
        for rec in self:
            total_invoiced = 0
            total_paid = 0
            for invoice in rec.invoice_ids.filtered(lambda x: x.state == 'posted'):
                if invoice.move_type == 'out_invoice':  # Regular invoices
                    total_invoiced += invoice.amount_total
                    total_paid += invoice.amount_total - invoice.amount_residual
                elif invoice.move_type == 'out_refund':  # Credit notes
                    total_invoiced -= invoice.amount_total
                    total_paid -= (
                                invoice.amount_total - invoice.amount_residual)

            rec.amount_due = total_invoiced - total_paid

    def action_open_business_doc(self):
        """ This method is called by the payment widget to open the payment or journal entry. """
        self.ensure_one()
        move = self.env['account.move'].browse(self.id)
        if move.exists():
            return move.action_open_business_doc()
        return False

    def js_remove_outstanding_partial(self, partial_id):
        """ Called by the 'payment' widget to remove a reconciled entry to the
        present invoice.

        :param partial_id: The id of an existing partial reconciled with the
        current invoice.
        """
        self.ensure_one()
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        return partial.unlink()

    @api.depends('invoice_ids.invoice_payments_widget')
    def _compute_payment_details(self):
        """ Compute the payment details from invoices and added into the sale
        order form view. """
        for rec in self:
            payment = []
            rec.payment_details = False
            if rec.invoice_ids:
                for line in rec.invoice_ids:
                    if line.invoice_payments_widget and 'content' in line.invoice_payments_widget:
                        for pay in line.invoice_payments_widget['content']:
                            payment.append(pay)
                for line in rec.invoice_ids:
                    if line.invoice_payments_widget:
                        payment_line = dict(line.invoice_payments_widget)
                        payment_line['content'] = payment
                        rec.payment_details = payment_line
                        break

    def action_register_payment(self):
        """ Open the account.payment.register wizard to pay the selected journal
         entries.
        :return: An action opening the account.payment.register wizard.
        """
        self.ensure_one()
        return {
            'name': self.env._('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.invoice_ids.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
