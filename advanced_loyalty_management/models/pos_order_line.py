# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.tools import float_round


class PosOrderLine(models.Model):
    """To Show the redeemed points in the redemption history"""
    _inherit = 'pos.order.line'

    points_remaining = fields.Float(string="Points Remaining",
                                    help="Remaining points after claming the "
                                         "reward")

    @api.model
    def remaining_points(self, balance, token):
        """Remaining points calculated after claiming the reward"""
        order = self.env['pos.order'].search([('access_token', '=', token[0])])
        pos_order_line = self.env['pos.order.line'].search(
            [('is_reward_line', '=', 'true'), ('order_id', '=', order.id)])
        pos_order_line.points_remaining = balance[0]

    def _apply_reward_points_rounding(self, points, reward):
        """Apply the custom rounding configured on Redemption rewards."""
        if not reward or not reward.rounding_mode:
            return points
        rounding_method = {
            'normal': 'HALF-UP',
            'up': 'UP',
            'down': 'DOWN',
        }.get(reward.rounding_mode, 'HALF-UP')
        return float_round(
            points,
            precision_digits=reward.rounding_precision or 0,
            rounding_method=rounding_method,
        )

    def _line_qualifies_for_program_rule(self, line, rule, program):
        """Mirror the POS points computation for Redemption program rounding."""
        if not (rule.any_product or line.product_id.id in rule.valid_product_ids.ids):
            return False
        if not line.is_reward_line:
            return True
        reward = line.reward_id
        if not reward:
            return False
        if reward.reward_type == 'discount' and reward.program_id.trigger == 'auto':
            return False
        if reward.program_id == program or reward.program_id.program_type in ('gift_card', 'ewallet'):
            return False
        return True

    def _compute_program_points_raw(self, order, program):
        """Recompute raw points before custom Redemption rounding is applied."""
        points = 0.0
        order_lines = order.lines
        for rule in program.rule_ids:
            eligible_lines = order_lines.filtered(
                lambda line: self._line_qualifies_for_program_rule(line, rule, program)
            )
            amount_with_tax = sum(eligible_lines.mapped('price_subtotal_incl'))
            amount_without_tax = sum(eligible_lines.mapped('price_subtotal'))
            amount_check = (
                amount_with_tax
                if rule.minimum_amount_tax_mode == 'incl' and amount_with_tax
                else amount_without_tax
            )
            if rule.minimum_amount > amount_check:
                continue
            total_product_qty = sum(
                eligible_lines.filtered(lambda line: not line.is_reward_line).mapped('qty')
            )
            if total_product_qty < rule.minimum_qty:
                continue
            if rule.reward_point_mode == 'order':
                points += rule.reward_point_amount
            elif rule.reward_point_mode == 'money':
                points += float_round(
                    rule.reward_point_amount * amount_with_tax,
                    precision_digits=2,
                    rounding_method='HALF-UP',
                )
            elif rule.reward_point_mode == 'unit':
                points += rule.reward_point_amount * total_product_qty
        return points

    @api.model
    def deduct_loyalty_points(self, coupon_id, points_spent, token):
        """Deduct all claimed reward points from the order loyalty cards.

        The POS screen can contain multiple reward lines from different
        programs/cards. We therefore recompute the deduction from the saved
        order lines instead of relying on the last selected reward only.
        """
        order = self.env['pos.order'].search([('access_token', '=', token[0])], limit=1)
        if not order:
            return

        reward_lines = self.env['pos.order.line'].search([
            ('order_id', '=', order.id),
            ('is_reward_line', '=', True),
            ('coupon_id', '!=', False),
        ])
        if not reward_lines:
            return

        remaining_points = {}
        for loyalty_card in reward_lines.mapped('coupon_id').sudo():
            card_reward_lines = reward_lines.filtered(
                lambda line: line.coupon_id.id == loyalty_card.id
            )
            redemption_lines = card_reward_lines.filtered(
                lambda line: line.reward_id.reward_type == 'redemption'
            )

            loyalty_card.points -= sum(card_reward_lines.mapped('points_cost'))

            if redemption_lines:
                redemption_reward = redemption_lines[0].reward_id
                raw_points = self._compute_program_points_raw(
                    order,
                    loyalty_card.program_id,
                )
                correction_points = 0.0
                for redemption_line in redemption_lines:
                    discount_amount = abs(redemption_line.price_subtotal_incl)
                    for rule in loyalty_card.program_id.rule_ids:
                        if rule.reward_point_mode == 'money':
                            correction_points += (
                                discount_amount * rule.reward_point_amount
                            )

                initial_awarded_points = self._apply_reward_points_rounding(
                    raw_points,
                    redemption_reward,
                )
                corrected_awarded_points = self._apply_reward_points_rounding(
                    raw_points - correction_points,
                    redemption_reward,
                )
                loyalty_card.points += (
                    corrected_awarded_points - initial_awarded_points
                )

            remaining_points[loyalty_card.id] = loyalty_card.points

        for reward_line in reward_lines:
            reward_line.points_remaining = remaining_points.get(
                reward_line.coupon_id.id, reward_line.points_remaining
            )
        return remaining_points
