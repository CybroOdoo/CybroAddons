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
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteSalePurchaseLimit(WebsiteSale):
    """Inherit the website sale controller to enforce a minimum purchase limit.

    If enabled, any attempt to proceed past the cart (checkout, payment)
    is redirected back to /shop/cart with a warning message when the order
    total is below the configured minimum.
    """

    def _check_purchase_limit(self):
        """Check if the current cart meets the minimum purchase limit.

        Returns:
            tuple: (is_blocked: bool, limit: float)
                   is_blocked is True when the limit is active and not met.
        """
        ICP = request.env['ir.config_parameter'].sudo()
        enabled = ICP.get_bool('website_purchase_limit.enabled_limit')
        if not enabled:
            return False, 0.0

        limit = ICP.get_float('website_purchase_limit.purchase_limit')
        if not limit:
            return False, 0.0

        order = request.cart
        if not order or not order.website_order_line:
            return False, limit

        return order.amount_total < limit, limit

    @http.route()
    def shop_checkout(self, try_skip_step=None, **query_params):
        """Block checkout navigation when the cart total is below the limit."""
        is_blocked, limit = self._check_purchase_limit()
        if is_blocked:
            return request.redirect(
                f'/shop/cart?purchase_limit_error=1&limit={limit}'
            )
        return super().shop_checkout(
            try_skip_step=try_skip_step, **query_params
        )

    @http.route()
    def shop_payment(self, **post):
        """Block access to the payment page when the cart total is below the limit."""
        is_blocked, limit = self._check_purchase_limit()
        if is_blocked:
            return request.redirect(
                f'/shop/cart?purchase_limit_error=1&limit={limit}'
            )
        return super().shop_payment(**post)
