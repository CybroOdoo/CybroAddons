# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
from odoo import models


class SaleOrder(models.Model):
    """Extends the Sale Order model to handle subscription orders."""
    _inherit = 'sale.order'

    def _prepare_order_line_values(self, product_id, quantity, period=None,
                                   **kwargs):
        """Add Recurrence period in order lines."""
        values = super()._prepare_order_line_values(product_id, quantity,
                                                    **kwargs)
        product = self.env['product.product'].browse(product_id)
        if product.is_subscription:
            values.update({'subscription_interval_id': period.id})
        return values

    def _cart_update_order_line(self, product_id, quantity, order_line,
                                **kwargs):
        """Add corresponding recurrence period for subscription product in
         sale order line."""
        self.ensure_one()
        period = kwargs.get('period')
        if order_line and quantity <= 0:  # Remove zero or negative lines
            order_line.unlink()
            order_line = self.env['sale.order.line']
        elif order_line and period:
            # Create a new line with a different recurrence period for the
            # same subscription product.
            for rec in order_line:
                if (rec.product_id.id == product_id and
                        rec.subscription_interval_id.id != period.id):
                    order_line_values = self._prepare_order_line_values(
                        product_id, 1, **kwargs)
                    order_line = self.env['sale.order.line'].sudo().create(
                        order_line_values)
        elif order_line and not period:
            update_values = self._prepare_order_line_update_values(
                order_line, quantity, **kwargs)
            if update_values:
                self._update_cart_line_values(order_line, update_values)
        elif quantity >= 0:
            order_line_values = self._prepare_order_line_values(
                product_id, quantity, **kwargs)
            order_line = self.env['sale.order.line'].sudo().create(
                order_line_values)
        return order_line

    def action_confirm(self):
        """Super action confirm to send mail to subscription customer"""
        res = super(SaleOrder, self).action_confirm()
        subscription_order = self.env[
            'subscription.package'].search(
            [('sale_order_id', '=', self.id)])
        subscription_order.send_subscription_order_to_customer()
        return res
