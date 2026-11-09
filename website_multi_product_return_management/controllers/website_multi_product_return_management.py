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
from datetime import datetime
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CustomerRegistration(http.Controller):
    """Controller to handle return order requests from website portal."""

    @http.route('/sale_return', type='jsonrpc', auth="public", website=True)
    def sale_return(self, **kwargs):
        """Controller to create return order with debug logs"""
        if kwargs.get('vals'):
            lines = []
            so_id = False
            for line in kwargs.get('vals'):
                _logger.info("Processing return payload line: %s", line)
                order_id = line.get('order_id')
                if not order_id:
                    continue
                so_id = request.env['sale.order'].sudo().browse(int(order_id))
                qty = int(line.get('quantity', 0))
                d_qty = int(line.get('deli_qty', qty))
                reason = line.get('reason', '')
                product_id = line.get('product_id')
                if qty > 0 and product_id:
                    lines.append((0, 0, {
                        'product_id': int(product_id),
                        'received_qty': qty,
                        'quantity': d_qty,
                        'reason': reason
                    }))
            if so_id and lines:
                values = {
                    'partner_id': so_id.partner_id.id,
                    'sale_order_id': so_id.id,
                    'user_id': request.env.uid,
                    'create_date': datetime.now(),
                    'return_line_ids': lines,
                    'state': 'draft',
                }
                returned_product_ids = [l[2]['product_id'] for l in lines]
                stock_picks = request.env['stock.picking'].sudo().search([('origin', '=', so_id.name)])
                moves = stock_picks.mapped('move_ids').sudo().filtered(
                    lambda p: p.product_id.id in returned_product_ids
                )
                ret_order = request.env['sale.return'].sudo().create(values)
                _logger.info("Successfully created sale.return record ID: %s (Ref: %s)",
                             ret_order.id, ret_order.name)
                if moves:
                    moves[0].picking_id.return_order_id = ret_order.id
                    moves[0].picking_id.return_order_picking = False
                    _logger.info("Linked sale return %s to picking %s",
                                 ret_order.name, moves[0].picking_id.name)
                return True
        _logger.warning("Failed to create sale return request with kwargs: %s", kwargs)
        return False

    @http.route('/my/request-thank-you', website=True, page=True,
                auth='public', csrf=False)
    def maintenance_request_thanks(self):
        """Controller for return the thanks page for return confirmation."""
        return request.render(
            'website_multi_product_return_management.'
            'customers_request_thank_page')
