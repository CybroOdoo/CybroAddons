# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields,models, _
from odoo.tools.float_utils import float_round


class SaleOrder(models.Model):
    """Inherit the 'sale.order' model to overwrite the _compute_cart_info
        and _cart_update functions."""
    _inherit = 'sale.order'

    cart_quantity = fields.Float(string="Cart Quantity", compute='_compute_cart_info')


    @api.depends('order_line.product_uom_qty', 'order_line.product_id')
    def _compute_cart_info(self):
        """
        Making cart_quantity integer is avoided in order
        to represent it in decimal values
        """
        for order in self:
            total_qty = sum(
                order.mapped('website_order_line.product_uom_qty')
            )
            order.cart_quantity = order.cart_quantity = float_round(
                total_qty,
                precision_digits=1
        )

            order.only_services = all(
                line.product_id.type == 'service' for line in
                order.website_order_line)

    def _cart_add(self, product_id, quantity: float, *, uom_id, **kwargs) -> dict:
        """Add quantity of the given product to the current sales order.

        :param product_id: product id, as a `product.product` id.
        :param quantity: the quantity to add to the cart.
        :param kwargs: Additional parameters given to deeper method calls.
        :return: values used by the cart service to give feedback to the customer.
        """
        self.ensure_one()
        self = self.with_company(self.company_id)

        if not uom_id:
            uom_id = self.env['product.product'].browse(product_id).uom_id.id  # type: ignore
        if existing_sol := self._cart_find_product_line(product_id, uom_id=uom_id, **kwargs)[:1]:
            # If a matching line is found, update the existing line instead.
            return self._cart_update_line_quantity(
                line_id=existing_sol.id,  # type: ignore
                quantity=existing_sol.product_uom_qty + quantity,
                **kwargs,
            )
        quantity, warning = self._verify_updated_quantity(
            self.env['sale.order.line'],
            product_id,
            quantity,
            uom_id=uom_id,
            **kwargs,
        )
        order_line = self._create_new_cart_line(product_id, quantity, uom_id, **kwargs)
        # NOTE: the provided product_id should not be given after `_create_new_cart_line` call as it
        # could be different from the line's product_id (see variant generation logic in
        # `_prepare_order_line_values`).
        if warning:
            (order_line or self).shop_warning = warning

        if not self.env.context.get('skip_cart_verification'):
            self._verify_cart_after_update()

        return {
            'added_qty': quantity,
            'line_id': order_line.id,
            'quantity': quantity,
            'warning': warning,
        }

    def _cart_update_line_quantity(self, line_id: int, quantity: float, **kwargs) -> dict:
        """Update the quantity of a given line of the cart.

        :param line_id: line id, as a `sale.order.line` id.
        :param quantity: the updated quantity of the line.
        :param kwargs: Additional parameters given to deeper method calls.
        :return: values used by the cart service to give feedback to the customer.
        """
        if self:
            self.ensure_one()

        self = self.with_company(self.company_id)  # noqa: PLW0642

        if not (order_line := self.order_line.filtered(lambda sol: sol.id == line_id)):
            # If the line isn't found because of wrong parameters, or because the user updated
            # the cart in other tabs, a warning will be returned.
            # Note that if the cart is empty, the zero cart_quantity will trigger a page reload
            # and this warning won't be shown.
            return {
                'warning': _(
                    "We weren't able to update your cart. Please refresh your page before trying"
                    " again."
                )
            }
        if quantity > 0:
            quantity, warning = self._verify_updated_quantity(
                order_line,
                order_line.product_id.id,
                quantity,
                uom_id=order_line.product_uom_id.id,
                **kwargs,
            )
        else:
            # If the line will be removed anyway, there is no need to verify
            # the requested quantity update.
            warning = ''
        precision = order_line.product_uom_id.rounding

        added_qty = float_round(
            quantity - order_line.product_uom_qty,
            precision_rounding=precision
        )

        order_line = self._cart_update_order_line(order_line, quantity, **kwargs)
        if not self.env.context.get('skip_cart_verification'):
            self._verify_cart_after_update()

        if warning:
            (order_line or self).shop_warning = warning

        return {
            'added_qty': added_qty,
            'line_id': order_line.id,
            'quantity': quantity,
            'warning': warning,
        }
