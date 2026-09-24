# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """Inherit sale order to apply e-wallet credit limits."""
    _inherit = "sale.order"

    def _get_real_points_for_coupon(self, coupon, post_confirm=False):
        """Override to limit the spendable points based on the credit limit."""
        points = super()._get_real_points_for_coupon(coupon, post_confirm)
        if coupon.set_limit and coupon.balance_limit_amount <= 0.0:
            raise ValidationError(_("Your coupon limit has been exceeded. Please contact your manager."))

        self.ensure_one()
        points = min(coupon.balance_limit_amount, coupon.points) if coupon.set_limit else coupon.points
        if coupon.program_id.applies_on != 'future' and self.state not in ('sale', 'done'):
            pending_points = self.coupon_point_ids.filtered(lambda p: p.coupon_id == coupon).points
            points += pending_points
        used_points = sum(self.order_line.filtered(lambda l: l.coupon_id == coupon).mapped('points_cost'))
        points -= used_points
        return points

    def action_confirm(self):
        """Override action confirm to deduct the used credit limit."""
        res = super().action_confirm()
        coupon_updates = {}
        for line in self.order_line.filtered(lambda l: l.coupon_id and l.coupon_id.limit):
            coupon = line.coupon_id
            coupon_updates[coupon] = coupon_updates.get(coupon, 0) + line.points_cost
        for coupon, points_cost in coupon_updates.items():
            coupon.used_limit += points_cost
        return res

    def _action_cancel(self):
        """Override action cancel to restore the used credit limit."""
        res = super()._action_cancel()
        coupon_updates = {}
        for line in self.order_line.filtered(lambda l: l.coupon_id and l.coupon_id.limit):
            coupon = line.coupon_id
            coupon_updates[coupon] = coupon_updates.get(coupon, 0) + line.points_cost
        for coupon, points_cost in coupon_updates.items():
            coupon.used_limit -= points_cost
        return res
