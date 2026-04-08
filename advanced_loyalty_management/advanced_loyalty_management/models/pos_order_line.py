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

            loyalty_card.points -= sum(card_reward_lines.mapped('points_cost'))

            redemption_lines = card_reward_lines.filtered(
                lambda line: line.reward_id.reward_type == 'redemption'
            )
            for redemption_line in redemption_lines:
                discount_amount = abs(redemption_line.price_subtotal_incl)
                for rule in loyalty_card.program_id.rule_ids:
                    if rule.reward_point_mode == 'money':
                        loyalty_card.points -= discount_amount * rule.reward_point_amount

            remaining_points[loyalty_card.id] = loyalty_card.points

        for reward_line in reward_lines:
            reward_line.points_remaining = remaining_points.get(
                reward_line.coupon_id.id, reward_line.points_remaining
            )
