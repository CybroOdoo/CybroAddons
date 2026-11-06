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
#############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleInherit(WebsiteSale):
    """Hide price, add to cart and quantity for public visitors."""

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>'
        '/page/<int:page>',
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False,
             **post):  # pylint: disable=too-many-arguments,too-many-positional-arguments
        """Flag whether the cart should be hidden on the shop page."""
        res = super().shop(page, category, search, min_price,
                           max_price, ppg, **post)
        hide_cart = request.env['ir.config_parameter'].sudo().get_str(
            'website_hide_button.hide_cart')
        is_public = request.env.user._is_public()  # pylint: disable=protected-access
        res.qcontext.update({'login_user': bool(is_public and hide_cart)})
        return res

    @http.route()
    def shop_payment(self, **post):
        """Restrict public visitors from accessing the payment page so
        that sale order creation is disabled."""
        user = request.env.user
        is_public = user._is_public()  # pylint: disable=protected-access
        is_portal = not is_public and user.has_group('base.group_portal')
        if is_portal or user.has_group('base.group_user'):
            return super().shop_payment(**post)
        return request.redirect("/")
