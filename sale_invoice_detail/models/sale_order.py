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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    """Inherited model sale.order to display invoice and payment details."""

    _inherit = 'sale.order'

    invoiced_amount = fields.Monetary(
        string='Invoiced Amount',
        compute='_compute_invoice_amount',
        currency_field='currency_id',
        help='Invoiced Amount for the Order',
    )
    due_amount = fields.Monetary(
        string='Due Amount',
        compute='_compute_invoice_amount',
        currency_field='currency_id',
        help='Due amount in the invoice',
    )
    paid_amount = fields.Monetary(
        string='Paid Amount',
        compute='_compute_invoice_amount',
        currency_field='currency_id',
        help='Paid amount for the order',
    )
    payment_count = fields.Integer(
        string='Payment Count',
        compute='_compute_invoice_amount',
        help='Payment Count',
    )
    paid_amount_percent = fields.Float(
        string='Paid Amount in %',
        compute='_compute_paid_amount_percent',
        help='Paid amount in percentage',
    )

    @api.depends(
        'invoice_ids',
        'invoice_ids.state',
        'invoice_ids.payment_state',
        'invoice_ids.amount_total',
        'invoice_ids.amount_residual',
        'invoice_ids.move_type',
        'invoice_ids.name',
        'order_line.invoice_lines',
    )
    def _compute_invoice_amount(self):
        """Compute invoiced, paid, and due amounts along with payment count."""
        for rec in self:
            order_sudo = rec.sudo()
            posted_out_invoices = order_sudo.invoice_ids.filtered(
                lambda inv: inv.state == 'posted'
                and inv.move_type == 'out_invoice'
                and (not rec.company_id or inv.company_id == rec.company_id)
            )
            posted_refund_invoices = order_sudo.invoice_ids.filtered(
                lambda inv: inv.state == 'posted'
                and inv.move_type == 'out_refund'
                and (not rec.company_id or inv.company_id == rec.company_id)
            )

            rec.invoiced_amount = sum(posted_out_invoices.mapped('amount_total')) - sum(
                posted_refund_invoices.mapped('amount_total')
            )

            if not posted_out_invoices:
                rec.paid_amount = 0.0
                rec.due_amount = 0.0
                rec.payment_count = 0
                continue

            payments = order_sudo._get_order_payments()
            rec.payment_count = len(payments)

            # Calculate paid amount via invoice residuals (handles partials, credit notes, grouped payments)
            residual_due = sum(posted_out_invoices.mapped('amount_residual')) - sum(
                posted_refund_invoices.mapped('amount_residual')
            )
            residual_paid = rec.invoiced_amount - max(0.0, residual_due)
            payments_amount = sum(payments.mapped('amount'))

            # Handle both reconciled payments and memo-matched payments
            computed_paid = max(residual_paid, payments_amount)
            if rec.invoiced_amount > 0:
                rec.paid_amount = min(rec.invoiced_amount, max(0.0, computed_paid))
                rec.due_amount = max(0.0, rec.invoiced_amount - rec.paid_amount)
            else:
                rec.paid_amount = 0.0
                rec.due_amount = 0.0

    @api.depends('amount_total', 'paid_amount')
    def _compute_paid_amount_percent(self):
        """Compute paid amount percentage relative to sale order amount_total."""
        for rec in self:
            if rec.amount_total:
                rec.paid_amount_percent = (rec.paid_amount / rec.amount_total) * 100.0
            else:
                rec.paid_amount_percent = 0.0

    # -------------------------------------------------------------------------
    # Helper & Action Methods
    # -------------------------------------------------------------------------

    def _get_order_payments(self):
        """Helper method to return all payments associated with the order's posted invoices.
        Validates caller read access on the order and enforces company isolation.
        """
        self.ensure_one()
        self.check_access('read')

        # Safely retrieve invoices associated with this order
        try:
            invoices = self.invoice_ids
            # Force fetch under caller environment to verify record-level access
            invoices.fetch(['state', 'move_type', 'company_id', 'name'])
            if not invoices and self.sudo().invoice_ids:
                invoices = self.sudo().invoice_ids
        except Exception:
            # Fallback to order_sudo if the salesperson lacks direct access to invoices created by accounting
            invoices = self.sudo().invoice_ids

        posted_invoices = invoices.filtered(
            lambda inv: inv.state == 'posted'
            and inv.move_type in ('out_invoice', 'out_refund')
            and (not self.company_id or inv.company_id == self.company_id)
        )
        if not posted_invoices:
            return self.env['account.payment']

        # Reconciled payments from invoice move lines
        reconciled_payments = posted_invoices.sudo()._get_reconciled_payments()
        if self.company_id:
            reconciled_payments = reconciled_payments.filtered(
                lambda p: not p.company_id or p.company_id == self.company_id
            )

        # Memo-matched payments within the order's company
        invoice_names = [inv.name for inv in posted_invoices if inv.name]
        memo_payments = self.env['account.payment'].sudo()
        if invoice_names:
            domain = [
                ('memo', 'in', invoice_names),
                ('state', 'in', ('paid', 'in_process', 'posted')),
            ]
            if self.company_id:
                domain.append(('company_id', '=', self.company_id.id))
            memo_payments = self.env['account.payment'].sudo().search(domain)

        payments = (reconciled_payments | memo_payments)
        return payments.with_env(self.env) if self.env['account.payment'].has_access('read') else payments

    def action_view_payments(self):
        """Action returning the customer payments linked to the order."""
        self.ensure_one()
        self.check_access('read')
        try:
            invoices = self.invoice_ids
            invoices.fetch(['state', 'move_type', 'company_id', 'name'])
            if not invoices and self.sudo().invoice_ids:
                invoices = self.sudo().invoice_ids
        except Exception:
            invoices = self.sudo().invoice_ids

        posted_invoices = invoices.filtered(
            lambda inv: inv.state == 'posted'
            and inv.move_type in ('out_invoice', 'out_refund')
            and (not self.company_id or inv.company_id == self.company_id)
        )
        if not posted_invoices:
            return None
        payment_ids = self._get_order_payments()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "domain": [('id', 'in', payment_ids.ids)],
            "context": {"create": False},
            "name": self.env._("Customer Payments"),
            'view_mode': 'list,form',
        }
