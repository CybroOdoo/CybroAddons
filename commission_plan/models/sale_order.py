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

from contextvars import ContextVar
from functools import wraps

from odoo import api, fields, models

from .account_move import PAID_PAYMENT_STATES


_COMMISSION_REBUILD_ORDER_IDS = ContextVar(
    'commission_rebuild_order_ids', default=frozenset())


def _prevent_reentrant_commission_rebuild(method):
    """Skip a nested commission rebuild for an order already in progress."""
    @wraps(method)
    def wrapper(records, *args, **kwargs):
        active_order_ids = _COMMISSION_REBUILD_ORDER_IDS.get()
        if active_order_ids.intersection(records.ids):
            return
        token = _COMMISSION_REBUILD_ORDER_IDS.set(
            active_order_ids | frozenset(records.ids))
        try:
            return method(records, *args, **kwargs)
        finally:
            _COMMISSION_REBUILD_ORDER_IDS.reset(token)
    return wrapper


class SaleOrder(models.Model):
    """Model sale.order is inherited to add commission lines"""
    _inherit = 'sale.order'

    commission_line_ids = fields.One2many('sale.order.commission', 'order_id',
                                          readonly=True)
    commission_amount = fields.Monetary(compute='_compute_commission_amount',
                                        store=True)

    @api.depends('commission_line_ids.amount')
    def _compute_commission_amount(self):
        """Compute the total commission amount for the sale order."""
        for order in self:
            order.commission_amount = sum(order.commission_line_ids.mapped(
                'amount'))

    def action_confirm(self):
        """Update commission lines when the sale order is confirmed."""
        result = super().action_confirm()
        self._update_commission_lines()
        return result

    def _create_invoices(self, grouped=False, final=False, date=None):
        """Update commission lines when the sale order is invoiced."""
        invoices = super()._create_invoices(grouped=grouped, final=final,
                                            date=date)
        self._update_commission_lines()
        return invoices

    def _is_commission_eligible(self):
        """A sale order only earns commission once every posted customer
        invoice raised against it has been fully paid. Orders with no
        posted invoice yet are not eligible.

        Uses the shared PAID_PAYMENT_STATES (which includes 'reversed') so
        that a credit note fully reversing an invoice -- which is how
        returns are meant to be reflected, via a separate negative return
        commission line -- never flips the whole order back to
        "ineligible" and wipes every commission line (earned and return
        alike) as a side effect.
        """
        self.ensure_one()
        invoices = self.invoice_ids.filtered(
            lambda inv: inv.move_type == 'out_invoice' and
            inv.state == 'posted')
        if not invoices:
            return False
        return all(
            inv.payment_state in PAID_PAYMENT_STATES for inv in invoices)

    # ------------------------------------------------------------------
    # Commission split (crm.team.commission_split: direct / equal) -- who
    # the already-calculated commission is paid to.
    # ------------------------------------------------------------------
    def _get_commission_split_team_members(self, team):
        """Return the res.users that count as members of `team` for Equal
        splitting.

        Uses crm.team's own `member_ids` (the actual team-membership
        mechanism in Odoo -- backed by crm.team.member / a user's
        sale_team_id) rather than assuming its meaning. The order's own
        salesperson is always folded in even if, for whatever reason,
        they are not (or no longer) a formal team member: excluding them
        would silently drop their share of a commission they themselves
        earned, which is worse than letting them share alongside the
        rest of the team.
        """
        self.ensure_one()
        members = team.member_ids
        if self.user_id and self.user_id not in members:
            members |= self.user_id
        return members

    @api.model
    def _allocate_amount_equally(self, amount, user_ids, currency):
        """Split `amount` equally across `user_ids` and return
        [{'user_id': id, 'amount': value}, ...].

        Uses the currency's own rounding (largest-remainder method:
        round every share first, then hand out any leftover cents one at
        a time to whichever shares were rounded down the most) so the
        allocations always sum EXACTLY back to `amount` -- rounding must
        never create or lose commission value.
        """
        ids = list(user_ids)
        if not ids:
            return []
        currency = currency or self.env.company.currency_id
        raw = {i: amount / len(ids) for i in ids}
        rounded = {i: currency.round(raw[i]) for i in ids}

        precision = currency.rounding or 0.01
        remainder = currency.round(amount - sum(rounded.values()))
        if remainder:
            units = int(round(abs(remainder) / precision))
            step = precision if remainder > 0 else -precision
            # remainder > 0: give the leftover cents to whichever shares
            # were rounded DOWN the most (largest raw - rounded first).
            # remainder < 0: take them back from whichever shares were
            # rounded UP the most (smallest/most negative raw - rounded
            # first) -- so sort direction flips with the remainder's sign.
            order_ids = sorted(
                ids, key=lambda i: (raw[i] - rounded[i]),
                reverse=(remainder > 0))
            for k in range(units):
                i = order_ids[k % len(order_ids)]
                rounded[i] = currency.round(rounded[i] + step)

        return [{'user_id': i, 'amount': rounded[i]} for i in ids]

    def _get_commission_split_allocations(self, amount):
        """Split an already-calculated commission `amount` for this sale
        order across users, according to order.team_id.commission_split.

        Returns a list of dicts: [{'user_id': ..., 'amount': ...}, ...]
        whose amounts always sum EXACTLY to `amount` after rounding. The
        commission calculation itself (product/category/straight/
        graduated rules, caps, ...) must already be finished before this
        is called -- this only decides who receives it.
        """
        self.ensure_one()
        team = self.team_id
        # No team, or an explicit/missing (falsy, e.g. on records created
        # before this field existed) split value: preserve the original,
        # pre-split behaviour -- the full amount goes to the salesperson
        # on the order. This is also the safe fallback when the order has
        # no salesperson to allocate to in the first place.
        split = team.commission_split if team else False
        if not split or split == 'direct' or not self.user_id:
            return [{'user_id': self.user_id.id, 'amount': amount}]

        members = self._get_commission_split_team_members(team)
        if not members:
            # No usable team members at all: fall back to the direct
            # behaviour rather than crashing or losing the commission.
            return [{'user_id': self.user_id.id, 'amount': amount}]

        currency = self.currency_id or self.company_id.currency_id
        return self._allocate_amount_equally(amount, members.ids, currency)

    def _apply_commission_split(self, values):
        """Expand a list of already-calculated commission value dicts
        (one per matched rule, each still carrying the order's
        salesperson as 'user_id' and the rule's full amount as 'amount')
        into one dict per split allocation.

        Only 'user_id' and 'amount' are replaced per allocation; every
        other computed field (product_id, category_id, revenue, rate,
        commission_id, team_id, ...) is copied unchanged onto every
        allocation line, since it describes the rule/basis the shared
        commission was calculated from, not any one recipient.
        """
        self.ensure_one()
        split_values = []
        for value in values:
            allocations = self._get_commission_split_allocations(
                value.get('amount', 0.0))
            for allocation in allocations:
                split_values.append(dict(
                    value, user_id=allocation['user_id'],
                    amount=allocation['amount']))
        return split_values

    @_prevent_reentrant_commission_rebuild
    def _update_commission_lines(self):
        """Recalculate persisted commissions for each order, idempotently.
        A commission line is only ever (re)created once the order's
        customer invoice(s) are fully paid -- an unpaid or partially
        invoiced order always has zero commission lines.

        The commission amount itself is always calculated first, exactly
        as before; commission_split only decides who the *already
        calculated* amount is paid to (see _apply_commission_split /
        _get_commission_split_allocations below).
        """
        Commission = self.env['sale.order.commission'].sudo()
        today = fields.Date.context_today(self)
        for order in self:
            # Do not rely on the order's cached one2many here. Payment-state
            # hooks rebuild these rows in a sudo environment, which can leave
            # an already-browsed order with stale commission IDs. Search the
            # database instead so every prior row is removed before rebuilding.
            Commission.search([('order_id', '=', order.id)]).unlink()
            order.invalidate_recordset(['commission_line_ids',
                                        'commission_amount'])
            if not order._is_commission_eligible():
                continue
            # A team plan takes precedence over an individual salesperson
            # plan. plan_source records exactly which of the two supplied
            # `plan` below, so it's visible on every commission line
            # rather than only being implicit in this resolution order.
            plan_source = 'team' if order.team_id.commission_id else 'user'
            plan = order.team_id.commission_id or order.user_id.commission_id
            order_date = order.date_order.date() if order.date_order else today
            if not plan or not order.user_id or not (
                    plan.date_from <= order_date <= plan.date_to):
                continue

            values = []
            revenue = sum(order.order_line.mapped('price_subtotal'))
            if plan.type == 'product':
                for rule in plan.product_comm_ids:
                    category_ids = rule.category_id.search([
                        ('id', 'child_of', rule.category_id.id)
                    ]).ids if rule.category_id else []
                    lines = order.order_line.filtered(
                        lambda line: (rule.product_id and
                                      line.product_id == rule.product_id) or
                        (category_ids and
                         line.product_id.categ_id.id in category_ids))
                    rule_revenue = sum(lines.mapped('price_subtotal'))
                    if not rule_revenue:
                        continue
                    amount = (rule_revenue * rule.percentage / 100
                              if rule.commission_amount_type == 'percentage'
                              else rule.fixed_amount)
                    if (rule.commission_amount_type == 'percentage' and
                            rule.amount and amount > rule.amount):
                        amount = rule.amount
                    values.append({
                        'user_id': order.user_id.id,
                        'team_id': order.team_id.id,
                        'commission_id': plan.id,
                        'plan_source': plan_source,
                        'product_id': rule.product_id.id,
                        'category_id': rule.category_id.id,
                        'revenue': rule_revenue,
                        'rate': rule.percentage,
                        'amount': amount,
                    })
            elif plan.revenue_type == 'straight':
                amount = (revenue * plan.straight_commission_rate / 100
                          if plan.straight_commission_type == 'percentage'
                          else plan.straight_commission_fixed)
                values.append({
                    'user_id': order.user_id.id,
                    'team_id': order.team_id.id,
                    'commission_id': plan.id,
                    'plan_source': plan_source,
                    'revenue': revenue,
                    'rate': plan.straight_commission_rate,
                    'amount': amount,
                })
            elif plan.revenue_type == 'graduated':
                rule = plan.revenue_grd_comm_ids.sorted('sequence').filtered(
                    lambda item: item.amount_from <= revenue and
                    (not item.amount_to or revenue <= item.amount_to))[:1]
                if rule:
                    rule = rule[0]
                    amount = (revenue * rule.graduated_commission_rate / 100
                              if rule.graduated_amount_type == 'percentage'
                              else rule.graduated_fixed_amount)
                    values.append({
                        'user_id': order.user_id.id,
                        'team_id': order.team_id.id,
                        'commission_id': plan.id,
                        'plan_source': plan_source,
                        'revenue': revenue,
                        'rate': rule.graduated_commission_rate,
                        'amount': amount,
                    })
            if values:
                # Commission rules/amounts above are untouched by
                # splitting; only *who* the amount is paid to changes.
                split_values = order._apply_commission_split(values)
                Commission.with_context(_commission_rebuild=True).create([
                    dict(value, order_id=order.id, commission_type='earned')
                    for value in split_values
                ])
                order.invalidate_recordset(['commission_line_ids',
                                            'commission_amount'])
            # Replay any posted credit notes against this order so returns
            # are reflected immediately, regardless of whether the earned
            # lines above were just (re)created or already existed.
            order._create_return_commission_lines()

    def _create_return_commission_lines(self):
        """(Re)create negative 'return' commission lines clawing back
        commission for posted credit notes issued against this order.

        This is called at the end of _update_commission_lines(), which has
        already wiped *all* of the order's commission lines (earned and
        return alike) and rebuilt the earned ones from scratch. So this
        method always rebuilds return lines from scratch too, replaying
        every currently-posted credit note tied to the order -- making the
        whole thing idempotent and safe to call as often as needed, the
        same way _update_commission_lines() already is.

        Each return line's amount is derived from the *same* rate/rule
        that produced the earned line it claws back (not a fresh plan
        lookup), and is prorated by how much of that rule's
        commissionable revenue was actually credited back. The total
        clawed back per earned line is capped so it can never exceed what
        was actually earned, even across several partial credit notes.
        """
        self.ensure_one()
        earned_lines = self.commission_line_ids.filtered(
            lambda line: line.commission_type == 'earned')
        if not earned_lines:
            return
        credit_notes = self.env['account.move'].sudo().search([
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_refund'),
            ('invoice_line_ids.sale_line_ids.order_id', '=', self.id),
        ], order='invoice_date, id')
        if not credit_notes:
            return

        Commission = self.env['sale.order.commission'].sudo()
        Category = self.env['product.category']
        # How much of each earned line's amount is still available to be
        # clawed back, across all the credit notes replayed below.
        remaining = {line.id: abs(line.amount) for line in earned_lines}

        for credit_note in credit_notes:
            note_lines = credit_note.invoice_line_ids.filtered(
                lambda line: self in line.sale_line_ids.order_id)
            if not note_lines:
                continue
            for earned in earned_lines:
                if not remaining[earned.id] or not earned.revenue:
                    continue
                if earned.product_id or earned.category_id:
                    category_ids = Category.search([
                        ('id', 'child_of', earned.category_id.id)
                    ]).ids if earned.category_id else []
                    rule_lines = note_lines.filtered(
                        lambda line: (earned.product_id and
                                      line.product_id == earned.product_id) or
                        (category_ids and
                         line.product_id.categ_id.id in category_ids))
                else:
                    # Revenue-wise (straight/graduated) plans aren't tied
                    # to a specific product, so the whole credit note's
                    # order-related lines count toward the return.
                    rule_lines = note_lines
                returned_revenue = sum(rule_lines.mapped('price_subtotal'))
                if not returned_revenue:
                    continue
                raw_claw = earned.amount * (returned_revenue / earned.revenue)
                claw = -min(abs(raw_claw), remaining[earned.id])
                if not claw:
                    continue
                remaining[earned.id] -= abs(claw)
                Commission.create({
                    'order_id': self.id,
                    'user_id': earned.user_id.id,
                    'team_id': earned.team_id.id,
                    'commission_id': earned.commission_id.id,
                    'plan_source': earned.plan_source,
                    'product_id': earned.product_id.id,
                    'category_id': earned.category_id.id,
                    'revenue': -returned_revenue,
                    'rate': earned.rate,
                    'amount': claw,
                    'commission_type': 'return',
                    'return_move_id': credit_note.id,
                    'origin_commission_id': earned.id,
                })
