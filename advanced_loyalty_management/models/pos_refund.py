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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    """To deduct the loyalty points when order is refunded"""
    _inherit = 'pos.order'

    @api.model
    def _load_pos_data_read(self, records, config):
        """Inject refunded_order_id into the POS session data for each order."""
        res = super()._load_pos_data_read(records, config)
        for record_vals in res:
            order = records.browse(record_vals['id'])
            if order.refunded_order_id:
                record_vals['refunded_order_id'] = order.refunded_order_id.id
        return res

    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        """Fix amount_return for refund orders where the frontend sends 0.00."""
        if not draft:
            total_paid = sum(order.payment_ids.mapped('amount'))
            expected_return = order.amount_total - total_paid

            from odoo.tools import float_is_zero
            if expected_return < 0 and float_is_zero(
                pos_order.get('amount_return', 0.0),
                precision_rounding=order.currency_id.rounding
            ):
                pos_order['amount_return'] = expected_return

        return super(PosOrder, self)._process_payment_lines(
            pos_order, order, pos_session, draft
        )

    @api.model
    def sync_from_ui(self, orders):
        """
        Override to process loyalty deduction for refund orders.

        The frontend never sends `couponPointChanges` for refund orders,
        so `confirm_coupon_programs` is never called for them.
        After the standard sync we detect refund orders and call
        `_process_refund_loyalty_deduction` to handle loyalty on the backend.
        """
        result = super().sync_from_ui(orders)

        synced_order_ids = [
            rec['id'] for rec in result.get('pos.order', []) if rec.get('id')
        ]
        if synced_order_ids:
            refund_orders = self.browse(synced_order_ids).filtered(
                lambda o: o.refunded_order_id and o.state in ('paid', 'done', 'invoiced')
            )
            refund_orders._process_refund_loyalty_deduction()

        return result

    def _compute_refund_points_for_program(self, program):
        """
        Mirrors the JS `_calculateOrderDeductions` logic in Python.

        For each rule in the program, computes how many points are lost
        for the products actually returned in `self` (the refund order).

        Returns the total points to deduct (float).
        """
        refund_lines = self.lines.filtered(
            lambda l: l.refunded_orderline_id and not l.refunded_orderline_id.is_reward_line
        )

        points_lost = 0.0

        for rule in program.rule_ids:
            if rule.reward_point_mode == 'order':
                # Only deduct if the ENTIRE original order is being refunded
                original_order = self.refunded_order_id
                if not original_order:
                    continue

                original_non_reward_lines = original_order.lines.filtered(
                    lambda l: not l.is_reward_line
                )
                total_original_qty = sum(abs(l.qty) for l in original_non_reward_lines)
                total_cumulative_refunded_qty = sum(
                    abs(l.refunded_qty) for l in original_non_reward_lines
                )
                current_refund_qty = sum(abs(l.qty) for l in refund_lines)
                previous_refund_qty = total_cumulative_refunded_qty - current_refund_qty

                EPSILON = 0.0001
                if (total_original_qty > EPSILON
                        and total_cumulative_refunded_qty >= (total_original_qty - EPSILON)
                        and previous_refund_qty < (total_original_qty - EPSILON)):
                    points_lost += rule.reward_point_amount

            elif rule.reward_point_mode in ('money', 'unit'):
                if rule.product_ids or rule.product_category_id or rule.product_tag_id or (rule.product_domain and rule.product_domain != '[]'):
                    valid_product_ids = set(rule._get_valid_products().ids)
                    valid_refund_lines = refund_lines.filtered(
                        lambda l: l.product_id.id in valid_product_ids
                    )
                else:
                    valid_refund_lines = refund_lines

                if not valid_refund_lines:
                    continue

                if rule.reward_point_mode == 'money':
                    for line in valid_refund_lines:
                        points_lost += rule.reward_point_amount * abs(line.price_subtotal_incl)
                else:  # unit
                    for line in valid_refund_lines:
                        points_lost += rule.reward_point_amount * abs(line.qty)

        return points_lost

    def _process_refund_loyalty_deduction(self):
        """
        Pure-backend loyalty deduction for refund orders.
        Computes proportional deduction per rule (not just copying original issued points).
        """
        LoyaltyHistory = self.env['loyalty.history']

        for order in self:
            original_order = order.refunded_order_id
            if not original_order:
                continue

            # Guard: skip if already processed for this refund order
            already_processed = LoyaltyHistory.search_count([
                ('order_id', '=', order.id),
                ('used', '>', 0),
            ])
            if already_processed:
                _logger.info("Refund %s already has loyalty deduction — skipping.", order.name)
                continue

            original_histories = LoyaltyHistory.search([
                ('order_id', '=', original_order.id),
                ('issued', '>', 0),
            ])

            for history in original_histories:
                card = history.card_id
                program = card.program_id

                points_to_deduct = order._compute_refund_points_for_program(program)

                if points_to_deduct <= 0:
                    continue

                before = card.points
                card.sudo().points -= points_to_deduct

                _logger.info(
                    "Refund %s: deducted %.2f pts from card %s [%s]. Balance: %.2f → %.2f",
                    order.name, points_to_deduct, card.id, program.name, before, card.points
                )

                LoyaltyHistory.create({
                    'card_id': card.id,
                    'order_model': self._name,
                    'order_id': order.id,
                    'description': f'Refund: Points reversed for {original_order.display_name}',
                    'used': points_to_deduct,
                    'issued': 0,
                })

    def add_loyalty_history_lines(self, coupon_data, coupon_updates):
        """
        Override to prevent core from writing issued=points/used=0 for refunds
        in the rare case the frontend DOES send coupon data.
        The main deduction is handled by `_process_refund_loyalty_deduction`
        in `sync_from_ui` which runs first.
        """
        is_refund = bool(self.refunded_order_id) or (self.amount_total < 0)

        if not is_refund:
            return super().add_loyalty_history_lines(coupon_data, coupon_updates)

        id_mapping = {
            item.get('old_id'): int(item.get('id'))
            for item in coupon_updates
        }
        history_lines_create_vals = []
        original_order = self.refunded_order_id

        for coupon in coupon_data:
            card_id = id_mapping.get(int(coupon['card_id']), False) or int(coupon['card_id'])
            loyalty_card = self.env['loyalty.card'].browse(card_id)
            if not loyalty_card.exists():
                continue

            cost = coupon.get('spent', 0)
            issued = coupon.get('won', 0)

            if card_id > 0 and (cost or issued):
                description = f"Refund: Points reversed for {original_order.display_name if original_order else self.display_name}"
                history_lines_create_vals.append({
                    'card_id': card_id,
                    'order_model': self._name,
                    'order_id': self.id,
                    'description': description,
                    'used': cost,
                    'issued': issued,
                })

        return self.env['loyalty.history'].create(history_lines_create_vals)