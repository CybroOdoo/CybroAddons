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
from odoo import models, fields


class PosOrder(models.Model):
    """To deduct the loyalty points when order is refunded"""
    _inherit = 'pos.order'

    check = fields.Boolean()

    def _compute_order_name(self):
        """Compute the loyalty points when order is refunded"""
        res = super()._compute_order_name()
        partner_id = self.partner_id
        li = [line.mapped('price_subtotal_incl') for line
              in self.lines.filtered(lambda x: not x.is_reward_line)]
        reward_line = self.refunded_order_ids.lines.filtered(
            lambda x: x.is_reward_line)
        points_cost = []
        for line in reward_line:
            dict = {}
            dict.update({
                line.coupon_id.id: line.points_cost
            })
            points_cost.append(dict)
        if self.refunded_order_ids:
            cards = self.env['loyalty.card'].search(
                [('partner_id', '=', partner_id.id)])

            for program in cards:
                if not self.refunded_order_ids.check:
                    for point in points_cost:
                        for key, values in point.items():
                            if program.id == key:
                                program.points += point[key]
                                self.refunded_order_ids.check = True

                for rule in program.program_id.rule_ids:
                    if rule.reward_point_mode == 'money':
                        points_granted = rule.reward_point_amount
                        reward_points = [sum(sublist) * points_granted for
                                         sublist in li]
                        program.points += reward_points[0]
                    elif rule.reward_point_mode == 'order':
                        reward_points = rule.reward_point_amount
                        reward_line_ids = len(reward_line)
                        ordered_qty = sum(self.refunded_order_ids.lines.mapped(
                            'qty')) - reward_line_ids
                        refunded_qty = sum(
                            self.refunded_order_ids.lines.filtered(
                                lambda x: not x.is_reward_line).mapped(
                                'refunded_qty'))
                        if ordered_qty == refunded_qty:
                            program.points -= reward_points
                    elif rule.reward_point_mode == 'unit':
                        points_granted = rule.reward_point_amount
                        qty = sum(
                            self.lines.filtered(
                                lambda x: not x.is_reward_line).mapped('qty'))
                        reward_points = qty * points_granted
                        program.points += reward_points
        return res
