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

import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ClickAndCollectPos(http.Controller):
    """Controller to manage Click & Collect configurations on website sale cart lines.

    Provides RPC endpoints allowing online customers to mark individual cart lines
    for in-store pickup and select their preferred POS pickup store.
    """

    @http.route(
        '/shop/cart/update_click_and_collect',
        type='jsonrpc',
        auth='public',
        website=True,
    )
    def update_click_and_collect(self, line_id, is_click_and_collect=None, pos_config_id=None):
        """Update Click & Collect preference and store selection for a cart line.

        Ensures security by validating that the requested order line belongs to the
        current user's active session cart before updating records.

        :param int line_id: ID of the sale.order.line to update.
        :param bool is_click_and_collect: True to enable in-store pickup, False otherwise.
        :param int|str pos_config_id: Selected POS store ID, or 'select'/False to clear.
        :return: Dict containing 'status' ('success' or 'error') and an optional error 'message'.
        :rtype: dict
        """
        order = getattr(request, 'cart', None)
        if not order:
            website = getattr(request.env, 'website', None)
            if website and hasattr(website, '_get_and_cache_current_cart'):
                order = website._get_and_cache_current_cart()

        if not order:
            return {'status': 'error', 'message': 'No active order found.'}

        line = order.order_line.filtered(lambda l: l.id == int(line_id))
        if not line:
            return {'status': 'error', 'message': 'Order line not found in cart.'}

        vals = {}
        if is_click_and_collect is not None:
            vals['is_click_and_collect'] = bool(is_click_and_collect)

        if pos_config_id is not None:
            if pos_config_id and str(pos_config_id) != 'select':
                pos_config = request.env['pos.config'].sudo().browse(int(pos_config_id))
                website = getattr(request.env, 'website', None)
                company_id = (
                    website.company_id.id
                    if website and website.company_id
                    else request.env.company.id
                )
                if pos_config.exists() and (
                    not pos_config.company_id or pos_config.company_id.id == company_id
                ):
                    vals['pos_config_id'] = pos_config.id
                else:
                    vals['pos_config_id'] = False
            else:
                vals['pos_config_id'] = False

        if vals.get('is_click_and_collect') is True and not vals.get('pos_config_id') and not line.pos_config_id:
            website = getattr(request.env, 'website', None)
            company_id = (
                website.company_id.id
                if website and website.company_id
                else request.env.company.id
            )
            single_store = request.env['pos.config'].sudo().search([
                ('company_id', '=', company_id)
            ], limit=2)
            if len(single_store) == 1:
                vals['pos_config_id'] = single_store.id

        if vals:
            line.sudo().write(vals)

        return {'status': 'success'}
