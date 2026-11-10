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
"""
Controller for handling website-related operations for the Beauty Shop theme,
specifically cart management.
"""
from odoo import http
from odoo.http import request


class BeautyShopSale(http.Controller):
    """cart_add Controller for managing shopping cart actions in the Beauty Shop theme."""

    @http.route(['/beauty/cart/clear'], type='http', auth='public',
                website=True, methods=['POST'], csrf=True)
    def cart_clear(self, **kw):
        """
        Clears the current user's shopping cart by removing all order lines.
        Uses Odoo's native sale_get_order() to locate the active cart so it
        is consistent with /shop/cart/update session management.
        """
        order = request.cart
        if order and order.state == 'draft':
            order.order_line.sudo().unlink()
        if hasattr(request, 'website') and hasattr(request.website, 'sale_reset'):
            request.website.sale_reset()
        if hasattr(request, 'session'):
            request.session['website_sale_cart_quantity'] = 0
            request.session.pop('website_sale_cart_quantity', None)
        return request.redirect('/shop/cart')
