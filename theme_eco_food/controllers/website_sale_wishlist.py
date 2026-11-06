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
"""Wishlist controller extensions for the Eco Food theme."""

# pylint: disable=import-error,no-name-in-module,protected-access
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.wishlist import ProductWishlist


class WebsiteSaleWishlist(ProductWishlist):
    """This function helps to override the functionalities of a wishlist"""

    # pylint: disable=too-few-public-methods

    @http.route(
        ["/shop/wishlist/add", "/shop/wishlist/add/<int:product_id>"],
        type="jsonrpc",
        auth="public",
        website=True,
    )
    def add_to_wishlist(self, product_id, **kw):
        """Avoid adding a product that is already in the current wishlist."""
        if kw.get("is_template"):
            product_id = (
                request.env["product.template"]
                .sudo()
                .browse(product_id)
                ._get_first_possible_variant_id()
            )
        wish = (
            request.env["product.wishlist"]
            .current()
            .filtered(lambda wishlist: wishlist.product_id.id == product_id)
        )
        return False if wish else super().add_to_wishlist(product_id, **kw)
