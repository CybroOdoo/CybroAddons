# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM @ cybrosys,(odoo@cybrosys.com)
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
import logging
from odoo import api, fields, models, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """ Inherit the 'sale.order' model to overwrite the _compute_cart_info
    and _cart_update functions."""
    _inherit = 'sale.order'

    cart_quantity = fields.Float(compute='_compute_cart_info',
                                 string='Cart Quantity', help="Cart Quantity "
                                                              "in eCommerce")

    @api.depends('order_line.product_uom_qty', 'order_line.product_id')
    def _compute_cart_info(self):
        """Making cart_quantity integer is avoided in order
        to represent it in decimal values"""
        for order in self:
            order.cart_quantity = float(sum(order.mapped
                                            ('website_order_line'
                                             '.product_uom_qty')))
            order.only_services = all(line.product_id.type == 'service'
                                      for line in order.website_order_line)

    def _cart_update(self, product_id, line_id=None, add_qty=0, set_qty=0,
                     **kwargs):
        """ Add or set product quantity, add_qty can be negative.
         Making add_qty and set_qty integer are avoided in order
         to represent them as decimal values."""
        self.ensure_one()
        product_context = dict(self.env.context)
        product_context.setdefault('lang', self.sudo().partner_id.lang)
        SaleOrderLineSudo = self.env['sale.order.line'].sudo().with_context(
            product_context)
        # Change lang to get correct name of attributes/values
        product_with_context = self.env['product.product'].with_context(
            product_context)
        product = product_with_context.browse(int(product_id)).exists()
        if not product or (
                not line_id and not product._is_add_to_cart_allowed()):
            raise UserError(
                _("The given product does not exist therefore it cannot "
                  "be added to cart."))
        try:
            if add_qty:
                add_qty = float(add_qty)
        except ValueError:
            add_qty = 1
        try:
            if set_qty:
                set_qty = float(set_qty)
        except ValueError:
            set_qty = 0
        quantity = 0
        order_line = False
        if self.state != 'draft':
            request.session['sale_order_id'] = None
            raise UserError(
                _('It is forbidden to modify a sales order which is not in '
                  'draft status.'))
        if line_id is not False:
            order_line = self._cart_find_product_line(product_id, line_id,
                                                      **kwargs)[:1]
        # Create line if no line with product_id can be located
        if not order_line:
            no_variant_attribute_values = kwargs.get(
                'no_variant_attribute_values') or []
            received_no_variant_values = product.env[
                'product.template.attribute.value'].browse(
                [int(ptav['value']) for ptav in no_variant_attribute_values])
            received_combination = \
                product.product_template_attribute_value_ids\
                | received_no_variant_values
            product_template = product.product_tmpl_id
            # Handle all cases where incorrect or incomplete data are received
            combination = product_template._get_closest_possible_combination(
                received_combination)
            # Get or create (if dynamic) the correct variant
            product = product_template._create_product_variant(combination)
            if not product:
                raise UserError(
                    _("The given combination does not exist therefore it "
                      "cannot be added to cart."))
            product_id = product.id
            values = self._website_product_id_change(self.id, product_id,
                                                     qty=1, **kwargs)
            # Add no_variant attributes that were not received
            for ptav in combination.filtered(
                    lambda ptav:
                    ptav.attribute_id.create_variant ==
                    'no_variant' and ptav not in received_no_variant_values):
                no_variant_attribute_values.append({
                    'value': ptav.id,
                })
            # Save no_variant attributes values
            if no_variant_attribute_values:
                values['product_no_variant_attribute_value_ids'] = [
                    (6, 0, [int(attribute['value']) for attribute in
                            no_variant_attribute_values])
                ]
            # Add is_custom attribute values that were not received
            custom_values = kwargs.get('product_custom_attribute_values') or []
            received_custom_values = product.env[
                'product.template.attribute.value'].browse(
                [int(ptav['custom_product_template_attribute_value_id']) for
                 ptav in custom_values])
            for ptav in combination.filtered(
                    lambda ptav:
                    ptav.is_custom and ptav not in received_custom_values):
                custom_values.append({
                    'custom_product_template_attribute_value_id': ptav.id,
                    'custom_value': '',
                })
            # Save is_custom attributes values
            if custom_values:
                values['product_custom_attribute_value_ids'] = [(0, 0, {
                    'custom_product_template_attribute_value_id': custom_value[
                        'custom_product_template_attribute_value_id'],
                    'custom_value': custom_value['custom_value']
                }) for custom_value in custom_values]
            # Create the line
            order_line = SaleOrderLineSudo.create(values)
            try:
                order_line._compute_tax_id()
            except ValidationError as e:
                # The validation may occur in backend (eg: taxcloud)
                # but should fail silently in frontend
                _logger.debug(
                    "ValidationError occurs during tax compute. %s" % (e))
            if add_qty:
                add_qty -= 1
        # Compute new quantity
        if set_qty:
            quantity = set_qty
        elif add_qty is not None:
            quantity = order_line.product_uom_qty + (add_qty or 0)
        # Remove zero of negative lines
        if quantity <= 0:
            linked_line = order_line.linked_line_id
            order_line.unlink()
            if linked_line:
                # Update description of the parent
                linked_product = product_with_context.browse(
                    linked_line.product_id.id)
                linked_line.name = \
                    linked_line.get_sale_order_line_multiline_description_sale(
                        linked_product)
        else:
            # Update line
            no_variant_attributes_price_extra = [
                ptav.price_extra for ptav in order_line
                .product_no_variant_attribute_value_ids]
            values = self.with_context(no_variant_attributes_price_extra=tuple(
                no_variant_attributes_price_extra))._website_product_id_change(
                self.id, product_id, qty=quantity, **kwargs)
            order = self.sudo().browse(self.id)
            if self.pricelist_id.discount_policy == 'with_discount' \
                    and not self.env.context.get('fixed_price'):
                product_context.update({
                    'partner': order.partner_id,
                    'quantity': quantity,
                    'date': order.date_order,
                    'pricelist': order.pricelist_id.id,
                })
            product_with_context = self.env['product.product'].with_context(
                product_context).with_company(order.company_id.id)
            product = product_with_context.browse(product_id)
            order_line.write(values)
            # Link a product to the sales order
            if kwargs.get('linked_line_id'):
                linked_line = SaleOrderLineSudo.browse(kwargs['linked_'
                                                              'line_id'])
                order_line.write({
                    'linked_line_id': linked_line.id,
                })
                linked_product = product_with_context.browse(
                    linked_line.product_id.id)
                linked_line.name = \
                    linked_line.get_sale_order_line_multiline_description_sale(
                     linked_product)
            order_line.name = \
                order_line.get_sale_order_line_multiline_description_sale(
                 product)
        option_lines = self.order_line.filtered(
            lambda l: l.linked_line_id.id == order_line.id)
        return {'line_id': order_line.id, 'quantity': quantity,
                'option_ids': list(set(option_lines.ids))}
