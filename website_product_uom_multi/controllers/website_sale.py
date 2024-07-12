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
import json
import logging

from odoo import fields, http
from odoo.http import request
from odoo.tools.json import scriptsafe as json_scriptsafe
from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale_product_configurator.controllers.website_sale import \
    WebsiteSale as WebsiteVariantSale


class WebsiteProductUom(WebsiteSale):
    """
    This class extends the WebsiteSale controller to include Unit of Measure
    (UOM) in the shopping cart update operations. It overrides the
    cart_update_json route to handle UOM-specific updates.
    """

    @http.route(['/shop/cart/update_json'], type='json', auth="public",
                methods=['POST'], website=True, csrf=False)
    def cart_update_json(
            self, product_id, line_id=None, add_qty=None, set_qty=None,
            display=True,
            product_custom_attribute_values=None,
            no_variant_attribute_values=None, uom_id=None, **kw
    ):

        """
        This route is called :
            - When changing quantity from the cart.
            - When adding a product from the wishlist.
            - When adding a product to cart on the same page (without redirection).
        """
        order = request.website.sale_get_order(force_create=True)

        if order.state != 'draft':
            request.website.sale_reset()
            if kw.get('force_create'):
                order = request.website.sale_get_order(force_create=True)
            else:
                return {}

        if product_custom_attribute_values:
            product_custom_attribute_values = json_scriptsafe.loads(
                product_custom_attribute_values)

        if no_variant_attribute_values:
            no_variant_attribute_values = json_scriptsafe.loads(
                no_variant_attribute_values)

        values = order._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            uom=uom_id,
            **kw
        )

        values['notification_info'] = self._get_cart_notification_information(
            order, [values['line_id']])
        values['notification_info']['warning'] = values.pop('warning', '')
        request.session['website_sale_cart_quantity'] = order.cart_quantity

        if not order.cart_quantity:
            request.website.sale_reset()
            return values

        values['cart_quantity'] = order.cart_quantity
        values['minor_amount'] = payment_utils.to_minor_currency_units(
            order.amount_total, order.currency_id
        ),
        values['amount'] = order.amount_total

        if not display:
            return values

        values['cart_ready'] = order._is_cart_ready()
        values['website_sale.cart_lines'] = request.env[
            'ir.ui.view']._render_template(
            "website_sale.cart_lines", {
                'website_sale_order': order,
                'date': fields.Date.today(),
                'suggested_products': order._cart_accessories()
            }
        )
        values['website_sale.total'] = request.env[
            'ir.ui.view']._render_template(
            "website_sale.total", {
                'website_sale_order': order,
            }
        )
        return values


class WebsiteProductVariant(WebsiteVariantSale):
    """
    This class extends the WebsiteVariantSale controller to handle the submission
    of optional product modals, ensuring that the Unit of Measure (UOM) is included
    in the cart update operations.
    """

    @http.route(
        '/shop/cart/update_option',
        type='json',
        auth='public',
        methods=['POST'],
        website=True,
        multilang=False,
    )
    def cart_options_update_json(self, product_and_options, lang=None,
                                 **kwargs):
        """This route is called when submitting the optional product modal.
            The product without parent is the main product, the other are options.
            Options need to be linked to their parents with a unique ID.
            The main product is the first product in the list and the options
            need to be right after their parent.
            product_and_options {
                'product_id',
                'product_template_id',
                'quantity',
                'parent_unique_id',
                'unique_id',
                'product_custom_attribute_values',
                'no_variant_attribute_values'
            }
        """
        if lang:
            request.website = request.website.with_context(lang=lang)

        order = request.website.sale_get_order(force_create=True)
        if order.state != 'draft':
            request.session['sale_order_id'] = None
            order = request.website.sale_get_order(force_create=True)

        product_and_options = json.loads(product_and_options)
        if product_and_options:
            # The main product is the first, optional products are the rest
            main_product = product_and_options[0]
            values = order._cart_update(
                product_id=main_product['product_id'],
                add_qty=main_product['quantity'],
                product_custom_attribute_values=main_product[
                    'product_custom_attribute_values'],
                no_variant_attribute_values=main_product[
                    'no_variant_attribute_values'],
                uom=main_product['uom_id'],
                **kwargs
            )

            line_ids = [values['line_id']]

            if values['line_id']:
                # Link option with its parent iff line has been created.
                option_parent = {main_product['unique_id']: values['line_id']}
                for option in product_and_options[1:]:
                    parent_unique_id = option['parent_unique_id']
                    option_values = order._cart_update(
                        product_id=option['product_id'],
                        set_qty=option['quantity'],
                        linked_line_id=option_parent[parent_unique_id],
                        product_custom_attribute_values=option[
                            'product_custom_attribute_values'],
                        no_variant_attribute_values=option[
                            'no_variant_attribute_values'],
                        **kwargs
                    )
                    option_parent[option['unique_id']] = option_values[
                        'line_id']
                    line_ids.append(option_values['line_id'])

            values[
                'notification_info'] = self._get_cart_notification_information(
                order, line_ids)

        values['cart_quantity'] = order.cart_quantity
        request.session['website_sale_cart_quantity'] = order.cart_quantity

        return values
