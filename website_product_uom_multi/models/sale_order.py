# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.info)
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

        if line_id:
            # If we have a line_id, we just fetch it
            order_line = self.env['sale.order.line'].browse(line_id).exists()
        else:
            # If no line_id, we search for a matching line. 
            # In Odoo 19, the second argument to _cart_find_product_line is uom_id.
            # We use our override to find the line and allow UOM changes.
            order_line = self._cart_find_product_line(product_id, uom_id=uom_id.id, **kwargs)[:1]

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
                uom_id=uom_id.id,
                **kwargs,
            )
        else:
            warning = ''

        self._remove_delivery_line()

        # Update the line using our custom helper
        order_line = self._cart_update_order_line(order_line, quantity, uom_id=uom_id,
                                                  product_id=product_id, **kwargs)

        if (order_line and order_line.price_unit == 0 and self.website_id.prevent_zero_price_sale
                and product.detailed_type not in self.env['product.template']._get_product_types_allow_zero_price()
        ):
            raise UserError(_(
                "The given product does not have a price therefore it cannot be added to cart.",
            ))

        return {
            'line_id': order_line.id,
            'quantity': quantity,
            'option_ids': list(set(order_line.linked_line_ids.filtered(
                lambda l: l.order_id == order_line.order_id).ids)),
            'warning': warning,
        }

    def _cart_find_product_line(self, product_id, uom_id=None, **kwargs):
        """ 
        Find the cart line matching the given parameters.
        Filter by UOM to allow different UOM variants of the same product
        to be added as separate lines.
        """
        self.ensure_one()
        lines = super()._cart_find_product_line(product_id, uom_id=uom_id, **kwargs)
        if uom_id:
            uom_id_val = uom_id.id if hasattr(uom_id, 'id') else uom_id
            lines = lines.filtered(lambda l: l.product_uom_id.id == uom_id_val)
        return lines

    def _cart_update_order_line(self, order_line, quantity, uom_id=None, product_id=None, **kwargs):
        """
        Update the order line in the cart based on the given quantity and UOM.
        """
        self.ensure_one()
        
        # Ensure we have recordsets for UOM and Product if possible
        if not uom_id and 'uom_id' in kwargs:
            uom_id = kwargs.get('uom_id')
        if isinstance(uom_id, int):
            uom_id = self.env['uom.uom'].browse(uom_id)
            
        if not product_id and 'product_id' in kwargs:
            product_id = kwargs.get('product_id')

        if order_line and quantity <= 0:
            order_line.unlink()
            return self.env['sale.order.line']

        if order_line:
            # Update existing line
            update_values = self._prepare_order_line_update_values(order_line, quantity, **kwargs)
            if uom_id and order_line.product_uom_id.id != uom_id.id:
                update_values['product_uom_id'] = uom_id.id
            if update_values:
                order_line.write(update_values)
                if uom_id and order_line.product_uom_id.id == uom_id.id:
                    # Recalculate price if UOM changed
                    order_line._compute_price_unit()
        elif quantity > 0 and product_id:
            # Create new line
            order_line_values = self._prepare_order_line_values(
                product_id, quantity, uom_id.id if uom_id else False, **kwargs
            )
            if uom_id:
                order_line_values['product_uom_id'] = uom_id.id
            order_line = self.env['sale.order.line'].sudo().create(order_line_values)
        return order_line
