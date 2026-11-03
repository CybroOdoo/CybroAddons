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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request


class DeliverySlotCart(http.Controller):
    """Routes used by the cart page to save the delivery date and slot."""

    @http.route(['/shop/cart/get_option'], type='jsonrpc', auth="public",
                website=True)
    def get_option(self, **kw):
        """Called when changing the slot timing ie office hours or home hours
        returns the option chosen"""
        option = kw.get('selected_option')
        slots = request.env['slot.time'].sudo().search(
            [('slot_type', '=', option)])
        return [[slot.id, slot.name] for slot in slots]

    @http.route(['/shop/cart/set_delivery_date'], type='jsonrpc',
                auth="public", website=True)
    def set_delivery_date(self, **kwargs):
        """Sets the delivery date for each order line of sale order created"""
        order = request.cart
        date = kwargs.get('delivery_date')
        line_id = int(kwargs.get('line_id'))
        line = order.order_line.filtered(lambda line: line.id == line_id)
        if line and date:
            line.sudo().delivery_date = date
        return {'success': request.env._('Delivery date updated.')}

    @http.route(['/shop/cart/set_delivery_slot'], type='jsonrpc',
                auth="public", website=True)
    def set_delivery_slot(self, **kwargs):
        """Sets the delivery slots for each order line of sale order created"""
        order = request.cart
        slot_id = int(kwargs.get('delivery_slot'))
        line_id = int(kwargs.get('line_id'))
        line = order.order_line.filtered(lambda line: line.id == line_id)
        slot = request.env['slot.time'].sudo().browse(slot_id).exists()
        if not line or not slot:
            return {'error': request.env._('Invalid delivery slot.'),
                    'error_type': 'invalid'}
        if not line.delivery_date:
            return {
                'error': request.env._(
                    'Select a delivery date for this order.'),
                'error_type': 'missing_date'}
        delivery_slot = request.env['delivery.slot'].sudo().with_context(
            active_test=False).search([
                ('slot_id', '=', slot.id),
                ('delivery_date', '=', line.delivery_date)], limit=1)
        if delivery_slot and delivery_slot.remaining_slots <= 0:
            return {
                'error': request.env._(
                    'This delivery slot has reached its capacity. '
                    'Choose another slot or date.'),
                'error_type': 'limit_reached'}
        line.sudo().write({
            'slot_id': slot.id,
            'delivery_slot_id': delivery_slot.id,
        })
        return {'success': request.env._('Delivery slot updated.')}
