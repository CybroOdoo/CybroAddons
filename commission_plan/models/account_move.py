# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models

# payment_state values that count as "paid" for commission purposes.
# 'in_payment' means a payment has been registered against the invoice but
# not yet reconciled with a bank statement -- treated as paid here since the
# salesperson has already earned the commission at that point.
# 'reversed' is the state Odoo puts a *previously paid* invoice into once a
# credit note fully reverses it -- it does NOT mean "never paid". It must
# stay in this set: SaleOrder._update_commission_lines() unlinks an order's
# commission lines up front and only recreates them (earned line + any
# return line) when the order is still "eligible". If 'reversed' were
# excluded, posting a full credit note would flip eligibility to False and
# both the earned line and its return clawback line would disappear
# entirely instead of the return line simply offsetting the earned one.
PAID_PAYMENT_STATES = ('paid', 'in_payment', 'reversed')


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _compute_payment_state(self):
        """payment_state is a stored *computed* field: registering or
        reconciling a payment triggers Odoo to recompute (and flush) it
        directly, never through write(). So this compute is the hook that
        actually fires when an invoice becomes paid in real usage.

        IMPORTANT: we deliberately do NOT read self.payment_state before
        calling super() to detect a "before/after" transition. This field
        is being computed for these exact records right now, so reading it
        mid-compute is undefined -- it can silently return a stale value,
        which was why the sync never actually fired even though the field
        itself ended up correct. Instead we just unconditionally resync
        afterwards, once the value is safe to read; _update_commission_lines
        is already idempotent (unlink-then-recreate) so this is cheap and
        correct even when nothing actually changed.
        """
        result = super()._compute_payment_state()
        self._sync_commission_with_payment_state()
        return result

    def write(self, vals):
        """Fallback for the less common case where payment_state is set
        directly via write() (e.g. data imports/migrations, other
        integrations) rather than through the normal reconciliation ->
        recompute path handled above.
        """
        result = super().write(vals)
        if 'payment_state' in vals:
            self._sync_commission_with_payment_state()
        return result

    def _post(self, soft=True):
        """Posting a credit note (return) is the point at which a return
        actually reduces commission -- draft credit notes are just a work
        in progress and must not affect anything yet.
        """
        posted = super()._post(soft=soft)
        # Re-filter on state rather than trusting the shape of what
        # super()._post() returns (it may exclude future-dated auto-post
        # moves that were left in draft) -- only truly posted moves should
        # ever trigger a return-commission replay.
        self.filtered(lambda move: move.state == 'posted'
                       )._sync_commission_with_return()
        return posted

    def button_draft(self):
        """Resetting a credit note to draft removes its effect on
        commission again (it's no longer posted, so it drops out of the
        replay in _create_return_commission_lines()).
        """
        result = super().button_draft()
        self._sync_commission_with_return()
        return result

    def button_cancel(self):
        """Cancelling a credit note likewise removes its effect on
        commission.
        """
        result = super().button_cancel()
        self._sync_commission_with_return()
        return result

    def _sync_commission_with_payment_state(self):
        """Sync commission with payment state."""
        # Creating stored commission rows can flush dependent invoice fields.
        # Do not re-enter a commission rebuild from that internal flush: the
        # outer rebuild is still in progress and will produce the final rows.
        if self.env.context.get('_commission_rebuild'):
            return
        orders = self.filtered(
            lambda move: move.move_type == 'out_invoice'
        ).invoice_line_ids.sale_line_ids.order_id
        if orders:
            orders._update_commission_lines()

    def _sync_commission_with_return(self):
        """A posted/un-posted/cancelled credit note (out_refund) never
        earns commission on its own -- it only ever claws back commission
        already earned on the original sale order(s) it credits. Route
        through the same full-rebuild entry point used for payments so
        earned and return lines always stay consistent with each other.
        """
        orders = self.filtered(
            lambda move: move.move_type == 'out_refund'
        ).invoice_line_ids.sale_line_ids.order_id
        if orders:
            orders._update_commission_lines()
