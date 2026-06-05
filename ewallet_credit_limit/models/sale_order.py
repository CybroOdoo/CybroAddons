# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
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

from odoo import models , _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """setting the limits and points from sale order"""
    _inherit = "sale.order"

    def action_confirm(self):
        """supering confirmation of sale order to update the limits to actual loyalty programs"""
        res = super().action_confirm()
        coupon_updates = {}
        for line in self.order_line.filtered(lambda l: l.coupon_id and l.coupon_id.limit):
            coupon = line.coupon_id
            coupon_updates[coupon] = coupon_updates.get(coupon, 0) + line.points_cost
        for coupon, points_cost in coupon_updates.items():
            coupon.balance_limit_amount -= points_cost
        return res

    def _get_real_points_for_coupon(self, coupon, post_confirm=False):
        """checking and raising validation if no balance limit or points"""
        if coupon.set_limit and coupon.balance_limit_amount <= 0.0:
            raise ValidationError(_("Your coupon limit has been exceeded. Please contact your manager."))
        super()._get_real_points_for_coupon(coupon, post_confirm)
        self.ensure_one()
        points = coupon.balance_limit_amount if coupon.set_limit == True else coupon.points
        if coupon.program_id.applies_on != 'future' and self.state not in ('sale', 'done'):
            pending_points = self.coupon_point_ids.filtered(lambda p: p.coupon_id == coupon).points
            points += pending_points
        used_points = sum(self.order_line.filtered(lambda l: l.coupon_id == coupon).mapped('points_cost'))
        points -= used_points
        return points
