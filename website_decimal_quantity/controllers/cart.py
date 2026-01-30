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
from odoo import fields
from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
from werkzeug.exceptions import NotFound
from odoo.tools import consteq
from odoo.tools.translate import _

from odoo.addons.payment import utils as payment_utils
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.cart import Cart

class Cart(Cart):

    @http.route()
    def add_to_cart(self,product_template_id,product_id,quantity=1.0,uom_id=None,product_custom_attribute_values=None,no_variant_attribute_value_ids=None,linked_products=None,
        **kwargs
    ):
        """ overrride the shopping cart.
        """
        order_sudo = request.cart or request.website._create_cart()
        quantity = float(quantity)  # allow float values in ecommerce

        product = request.env['product.product'].browse(product_id).exists()
        if not product or not product._is_add_to_cart_allowed():
            raise UserError(_(
                "The given product does not exist therefore it cannot be added to cart."
            ))

        added_qty_per_line = {}
        values = order_sudo.with_context(skip_cart_verification=True)._cart_add(
            product_id=product_id,
            quantity=quantity,
            uom_id=uom_id,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_value_ids=no_variant_attribute_value_ids,
            **kwargs,
        )
        line_ids = {product_template_id: values['line_id']}
        added_qty_per_line[values['line_id']] = values['added_qty']
        is_combo = product.type == 'combo'
        updated_line = (
            values['line_id']
            and order_sudo.order_line.filtered(lambda line: line.id == values['line_id'])
        ) or order_sudo.env['sale.order.line']

        if linked_products and values['line_id']:
            for product_data in linked_products:
                product_sudo = request.env['product.product'].sudo().browse(
                    product_data['product_id']
                ).exists()
                if product_data['quantity'] and (
                    not product_sudo
                    or (
                        not product_sudo._is_add_to_cart_allowed()
                        # For combos, the validity of the given product will be checked
                        # through the SOline constraints (_check_combo_item_id)
                        and not product_data.get('combo_item_id')
                    )
                ):
                    raise UserError(_(
                        "The given product does not exist therefore it cannot be added to cart."
                    ))
                product_values = order_sudo.with_context(skip_cart_verification=True)._cart_add(
                    product_id=product_data['product_id'],
                    quantity=product_data['quantity'],
                    uom_id=product_data.get('uom_id'),
                    product_custom_attribute_values=product_data['product_custom_attribute_values'],
                    no_variant_attribute_value_ids=[
                        int(value_id) for value_id in product_data['no_variant_attribute_value_ids']
                    ],
                    # Using `line_ids[...]` instead of `line_ids.get(...)` ensures that this throws
                    # if an optional product contains bad data.
                    linked_line_id=line_ids[product_data['parent_product_template_id']],
                    **self._get_additional_cart_update_values(product_data),
                    **kwargs,
                )
                if is_combo and not product_values.get('quantity'):
                    # Early return when one of the combo products if fully unavailable
                    # Delete main combo line (and existing children in cascade)
                    updated_line.unlink()
                    # Return empty notification since cart update is considered as failed
                    return {
                        'cart_quantity': order_sudo.cart_quantity,
                        'notification_info': {
                            'warning': product_values.get('warning', ''),
                        },
                        'quantity': 0,
                        'tracking_info': [],
                    }

                line_ids[product_data['product_template_id']] = product_values['line_id']
                added_qty_per_line[product_values['line_id']] = product_values['added_qty']

        warning = values.pop('warning', '')
        if is_combo and order_sudo._check_combo_quantities(updated_line):
            # If quantities were modified through `_check_combo_quantities`, the added qty per line
            # must be adapted accordingly, and the returned warning should be the final one saved
            # on the combo line.
            added_qty_per_line = {
                line.id: updated_line.product_uom_qty
                for line in (updated_line + updated_line.linked_line_ids)
            }
            warning = updated_line.shop_warning
            values['quantity'] = updated_line.product_uom_qty

        # Recompute delivery prices & other cart stuff (loyalty rewards)
        order_sudo._verify_cart_after_update()

        # The validity of a combo product line can only be checked after creating all of its combo
        # item lines.
        main_product_line = request.env['sale.order.line'].browse(values['line_id'])
        if main_product_line.product_type == 'combo':
            main_product_line._check_validity()
        return {
            'cart_quantity': values['quantity'],
            'notification_info': {
                **self._get_cart_notification_information(
                    order_sudo, added_qty_per_line
                ),
                'warning': warning,
            },
            'quantity': values.pop('quantity', 0),
            'tracking_info': self._get_tracking_information(order_sudo, line_ids.values()),
        }

    @http.route()
    def cart(self, id=None, access_token=None, revive_method='', **post):
        """ Display the cart page.

        This route is responsible for the main cart management and abandoned cart revival logic.

        :param str id: The abandoned cart's id.
        :param str access_token: The abandoned cart's access token.
        :param str revive_method: The revival method for abandoned carts. Can be 'merge' or 'squash'.
        :return: The rendered cart page.
        :rtype: str
        """
        order_sudo = request.cart

        values = {}
        if id and access_token:
            abandoned_order = request.env['sale.order'].sudo().browse(int(id)).exists()
            if not abandoned_order or not consteq(abandoned_order.access_token, access_token):  # wrong token (or SO has been deleted)
                raise NotFound()
            if abandoned_order.state != 'draft':  # abandoned cart already finished
                values.update({'abandoned_proceed': True})
            elif revive_method == 'squash' or (revive_method == 'merge' and not request.session.get('sale_order_id')):  # restore old cart or merge with unexistant
                request.session['sale_order_id'] = abandoned_order.id
                return request.redirect('/shop/cart')
            elif revive_method == 'merge':
                abandoned_order.order_line.write({'order_id': request.session['sale_order_id']})
                abandoned_order.action_cancel()
            elif abandoned_order.id != request.session.get('sale_order_id'):  # abandoned cart found, user have to choose what to do
                values.update({'id': abandoned_order.id, 'access_token': abandoned_order.access_token})

        values.update({
            'website_sale_order': order_sudo,
            'date': fields.Date.today(),
            'suggested_products': [],
        })
        if order_sudo:
            order_sudo.order_line.filtered(lambda sol: sol.product_id and not sol.product_id.active).unlink()
            values['suggested_products'] = order_sudo._cart_accessories()
            values.update(self._get_express_shop_payment_values(order_sudo))

        values.update(request.website._get_checkout_step_values())
        values.update(self._cart_values(**post))
        values.update(self._prepare_order_history())
        return request.render('website_sale.cart', values)

    @http.route()
    def update_cart(self, line_id, quantity, product_id=None, **kwargs):
        """Update the quantity of a specific line of the current cart.

               :param int line_id: line to update, as a `sale.order.line` id.
               :param float quantity: new line quantity.
                   0 or negative numbers will only delete the line, the ecommerce
                   doesn't work with negative numbers.
               :param int|None product_id: product_id of the edited line, only used when line_id
                   is falsy
               :params dict kwargs: additional parameters given to _cart_update_line_quantity calls.
               """
        order_sudo = request.cart
        quantity = float(quantity)  #allow float values in ecommerce
        IrUiView = request.env['ir.ui.view']

        # This method must be only called from the cart page BUT in some advanced logic
        # eg. website_sale_loyalty, a cart line could be a temporary record without id.
        # In this case, the line_id must be found out through the given product id.
        if not line_id:
            line_id = order_sudo.order_line.filtered(
                lambda sol: sol.product_id.id == product_id
            )[:1].id

        values = order_sudo._cart_update_line_quantity(line_id, quantity, **kwargs)
        values['cart_quantity'] = order_sudo.cart_quantity
        values['cart_ready'] = order_sudo._is_cart_ready()
        values['amount'] = order_sudo.amount_total
        values['minor_amount'] = (
                                         order_sudo and payment_utils.to_minor_currency_units(
                                     order_sudo.amount_total, order_sudo.currency_id
                                 )
                                 ) or 0.0
        values['website_sale.cart_lines'] = IrUiView._render_template(
            'website_sale.cart_lines', {
                'website_sale_order': order_sudo,
                'date': fields.Date.today(),
                'suggested_products': order_sudo._cart_accessories()
            }
        )
        values['website_sale.total'] = IrUiView._render_template(
            'website_sale.total', {
                'website_sale_order': order_sudo,
            }
        )
        values['website_sale.quick_reorder_history'] = IrUiView._render_template(
            'website_sale.quick_reorder_history', {
                'website_sale_order': order_sudo,
                **self._prepare_order_history(),
            }
        )
        return values

    def cart_quantity(self):
        if 'website_sale_cart_quantity' not in request.session:
            return request.website.sale_get_order().mapped(
                'website_order_line.product_uom_qty')
        return request.session['website_sale_cart_quantity']
