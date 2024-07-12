# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
################################################################################
from odoo import models, _
from odoo.exceptions import UserError
from odoo.http import request


class SaleOrder(models.Model):
    """
    Inherits the sale.order model to extend its functionality.
    """
    _inherit = 'sale.order'

    def _cart_update(self, product_id, line_id=None, add_qty=0, set_qty=0,
                     uom=None, **kwargs):
        """ Add or set product quantity, add_qty can be negative """
        self.ensure_one()
        self = self.with_company(self.company_id)

        if self.state != 'draft':
            request.session.pop('sale_order_id', None)
            request.session.pop('website_sale_cart_quantity', None)
            raise UserError(
                _('It is forbidden to modify a sales order which is not in draft status.'))

        product = self.env['product.product'].browse(product_id).exists()
        uom_id = self.env['uom.uom'].browse(uom)
        if add_qty and (not product or not product._is_add_to_cart_allowed()):
            raise UserError(
                _("The given product does not exist therefore it cannot be added to cart."))

        if line_id is not False:
            order_line = self._cart_find_product_line(product_id, line_id,
                                                      **kwargs)[:1]
            if uom_id :
                order_line_ids = order_line.order_id.order_line
                current_product_ids = order_line_ids.filtered(lambda l: l.product_id.id == product_id)
                if current_product_ids:
                    order_line = current_product_ids.filtered(lambda  n: n.product_uom.id == uom_id.id)

        else:
            order_line = self.env['sale.order.line']

        try:
            if add_qty:
                add_qty = int(add_qty)
        except ValueError:
            add_qty = 1

        try:
            if set_qty:
                set_qty = int(set_qty)
        except ValueError:
            set_qty = 0

        quantity = 0
        if set_qty:
            quantity = set_qty
        elif add_qty is not None:
            if order_line:
                quantity = order_line.product_uom_qty + (add_qty or 0)
            else:
                quantity = add_qty or 0

        if quantity > 0:
            quantity, warning = self._verify_updated_quantity(
                order_line,
                product_id,
                quantity,
                **kwargs,
            )
        else:
            # If the line will be removed anyway, there is no need to verify
            # the requested quantity update.
            warning = ''

        self._remove_delivery_line()

        order_line = self._cart_update_order_line(product_id, quantity,
                                                  order_line,uom_id, **kwargs)

        if (
                order_line
                and order_line.price_unit == 0
                and self.website_id.prevent_zero_price_sale
                and product.detailed_type not in self.env[
            'product.template']._get_product_types_allow_zero_price()
        ):
            raise UserError(_(
                "The given product does not have a price therefore it cannot be added to cart.",
            ))

        return {
            'line_id': order_line.id,
            'quantity': quantity,
            'option_ids': list(set(order_line.option_line_ids.filtered(
                lambda l: l.order_id == order_line.order_id).ids)),
            'warning': warning,
        }


    def _cart_update_order_line(self, product_id, quantity, order_line, uom_id, **kwargs):
        """
        Update the order line in the cart based on the given product,
        quantity, and UOM.
        """
        self.ensure_one()
        if order_line and quantity <= 0:
            # Remove zero or negative lines
            order_line.unlink()
            order_line = self.env['sale.order.line']
        elif order_line:
            # Update existing line
            update_values = self._prepare_order_line_update_values(order_line, quantity, **kwargs)
            if update_values:
                self._update_cart_line_values(order_line, update_values)
        elif quantity > 0:
            # Create new line
            order_line_values = self._prepare_order_line_values(product_id, quantity, **kwargs)
            if uom_id:
                order_line_values['product_uom'] = uom_id.id
            order_line = self.env['sale.order.line'].sudo().create(order_line_values)
        return order_line
