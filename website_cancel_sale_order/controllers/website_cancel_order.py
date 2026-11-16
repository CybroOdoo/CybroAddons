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
from odoo import _, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class SaleOrderCancel(CustomerPortal):
    """Controller to handle sale order cancellation."""

    @http.route(
        '/cancel/reason/edit',
        type='jsonrpc',
        auth='public',
        website=True,
    )
    def cancel_sale_order(self, sale_order_id=None, reason=None, access_token=None, **post):
        """Update cancellation reason and cancel the sale order."""
        sale_order_id = sale_order_id or post.get('sale_order_id')
        reason = reason or post.get('reason')
        access_token = access_token or post.get('access_token') or request.httprequest.args.get('access_token')

        if not sale_order_id:
            return {'error': _('Missing order identifier.')}

        try:
            order_id = int(sale_order_id)
        except (ValueError, TypeError):
            return {'error': _('Invalid order identifier.')}

        try:
            sale_order = self._document_check_access(
                'sale.order', order_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return {'error': _('Invalid order or access denied.')}

        if sale_order.state == 'cancel':
            return {'error': _('Order is already cancelled.')}

        sale_order.write({
            'is_cancel': True,
            'cancellation_reason': reason,
        })

        sale_order.with_context(
            disable_cancel_warning=True
        ).action_cancel()

        return {
            'success': True,
            'sale_order_id': sale_order.id,
        }
