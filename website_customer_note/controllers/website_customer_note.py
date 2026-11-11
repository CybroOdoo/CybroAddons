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


class WebsiteSaleCustomerNote(http.Controller):
    """Handle website sale customer note requests."""

    @http.route(
        '/shop/save_customer_note',
        type='jsonrpc',
        auth='public',
        website=True,
    )
    def save_customer_note(self, customer_note=None, order_id=None, **kwargs):
        """Save customer note to the active cart order before payment.

        Verifies that the target order matches the visitor's current session cart
        to prevent unauthorized tampering with arbitrary sale orders.
        """
        order_sudo = getattr(request, 'cart', None)
        if not order_sudo:
            return {'success': False, 'error': 'No active order found'}

        if order_id:
            try:
                if order_sudo.id != int(order_id):
                    return {'success': False, 'error': 'Access denied'}
            except (ValueError, TypeError):
                return {'success': False, 'error': 'Invalid order ID'}

        order_sudo.write({'customer_note': (customer_note or '').strip()})
        return {'success': True}
