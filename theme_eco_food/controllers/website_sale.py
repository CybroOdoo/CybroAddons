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
"""Shop controller extensions for the Eco Food theme."""

# pylint: disable=import-error,no-name-in-module
from odoo import http
from odoo.fields import Domain
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class EcoFoodWebsiteSale(WebsiteSale):
    """This function helps to override the functionalities of a website shop"""

    # pylint: disable=too-few-public-methods

    @http.route(
        "/theme_eco_food/product_selections",
        type="jsonrpc",
        auth="public",
        website=True,
    )
    def set_product_selections(self, all_products=False, category_ids=None):
        """Keep shop product selection in the current visitor's session."""
        if all_products:
            request.session.pop("theme_eco_food_category_ids", None)
            return True
        category_ids = [
            int(category_id)
            for category_id in (category_ids or [])
            if str(category_id).isdigit()
        ]
        request.session["theme_eco_food_category_ids"] = category_ids
        return True

    def _shop_lookup_products(self, options, post, search, website):
        """Apply visitor categories before native price, count and pager calculations."""
        category_ids = request.session.get("theme_eco_food_category_ids")
        if category_ids is not None:
            options = dict(options)
            options["extra_domain"] = Domain.AND(
                [
                    options.get("extra_domain") or Domain.TRUE,
                    Domain("public_categ_ids", "child_of", category_ids)
                    if category_ids
                    else Domain.FALSE,
                ]
            )
        return super()._shop_lookup_products(options, post, search, website)
