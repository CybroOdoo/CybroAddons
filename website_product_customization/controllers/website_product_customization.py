# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
import re
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.cart import Cart


class WebsiteProductCustomization(Cart):
    """Extension of Odoo's Cart controller to support custom product design
       handling during website cart operations.
    """

    @http.route(route='/shop/cart/add', type='jsonrpc', auth='public',
                methods=['POST'], website=True, sitemap=False)
    def add_to_cart(
        self,
        product_template_id,
        product_id,
        quantity,
        uom_id=None,
        product_custom_attribute_values=None,
        no_variant_attribute_value_ids=None,
        linked_products=None,
        design_image=None,
        **kwargs,
    ):
        """Override of the default add_to_cart route to include support for
        custom product design images."""

        # Call original controller logic
        res = super().add_to_cart(
            product_template_id=product_template_id,
            product_id=product_id,
            quantity=quantity,
            uom_id=uom_id,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_value_ids=no_variant_attribute_value_ids,
            linked_products=linked_products,
            **kwargs
        )

        order = request.cart
        if not order:
            return res

        if design_image:
            # Remove base64 header prefix if present
            image_base64 = re.sub(r'^data:image/\w+;base64,', '', design_image)

            # Find the line just added/updated.
            # Look for lines for this product, sorted by latest update.
            line = order.order_line.filtered(
                lambda line: line.product_id.id == int(product_id)
            )
            if line:
                last_line = line.sorted(key='write_date', reverse=True)[0]
                last_line.write({
                    'product_design': image_base64,
                    'is_customized_product': True,
                })

        return res
