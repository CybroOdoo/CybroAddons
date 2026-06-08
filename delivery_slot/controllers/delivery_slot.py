# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.payment.controllers.portal import PaymentPortal



class Cart(PaymentPortal):
    """Extends the WebsiteSale controller to add delivery slot functionality."""


    @http.route(['/shop/cart'], type='http', auth="public", website=True)
    def cart(self, **post):
        """Adding extra field to choose delivery date and slot for each cart lines"""
        val = super().cart(**post)
        is_delivery_slot = request.env['ir.config_parameter'].sudo().get_param(
            'delivery_slot.enable_delivery_date')
        slots = request.env['slot.time'].search([])
        slot_home = request.env['slot.time'].search([]).filtered(
            lambda l: l.slot_type == 'home')
        slot_office = request.env['slot.time'].search([]).filtered(
            lambda l: l.slot_type == 'office')
        val.qcontext.update({
            'is_delivery_slot': is_delivery_slot,
            'slots': slots,
            'slot_home': slot_home,
            'slot_office': slot_office,
        })
        return val

    @http.route(['/shop/cart/update'], type='jsonrpc', auth="public",
                methods=['POST'], website=True, csrf=False)
    def update_cart(self, **kw):
        """Passing delivery date and slot values"""
        val = super().update_cart(**kw)
        is_delivery_slot = request.env['ir.config_parameter'].sudo().get_param(
            'delivery_slot.enable_delivery_date')
        slots = request.env['slot.time'].search([])
        slot_home = request.env['slot.time'].search([]).filtered(
            lambda l: l.slot_type == 'home')
        slot_office = request.env['slot.time'].search([]).filtered(
            lambda l: l.slot_type == 'office')
        val.update({
            'is_delivery_slot': is_delivery_slot,
            'slots': slots,
            'slot_home': slot_home,
            'slot_office': slot_office,
        })
        return val

    @http.route(['/shop/cart/get_option'], type='jsonrpc', auth="public",
                website=True)
    def get_option(self, **kw):
        """Called when changing the slot timing ie office hours or home hours
        returns the option chosen"""
        option = kw.get('selected_option')
        slot_filtered = request.env['slot.time'].search([]).filtered(
            lambda l: l.slot_type == option)
        options = [[slot.id, slot.name] for slot in slot_filtered]
        return options

    @http.route(['/shop/cart/set_delivery_date'], type='jsonrpc', auth="public",
                website=True)
    def set_delivery_date(self, **kwargs):
        """Sets the delivery date for each order line of sale order created"""
        order = request.cart
        date = kwargs.get('delivery_date')
        line_id = int(kwargs.get('line_id'))
        for line in order.order_line:
            if line.id == line_id:
                if date:
                    line.delivery_date = date
        return {'success': 'Delivery date updated.'}

    @http.route(['/shop/cart/set_delivery_slot'], type='jsonrpc', auth="public",
                website=True)
    def set_delivery_slot(self, **kwargs):
        """Sets the delivery slots for each order line of sale order created"""
        order = request.cart
        slot_id = int(kwargs.get('delivery_slot'))
        line_id = int(kwargs.get('line_id'))
        slot = request.env['slot.time'].browse(slot_id)
        delivery_date = None
        for line in order.order_line:
            if line.id == line_id:
                delivery_date = line.delivery_date
                break
        if not delivery_date:
            return {'error': 'Select a delivery date for this order.',
                    'error_type': 'missing_date'}
        delivery_slot = request.env['delivery.slot'].search([
            ('slot_id', '=', slot_id),
            ('delivery_date', '=', delivery_date),
            ('active', '=', False),
            ('remaining_slots', '<=', 0)
        ], limit=1)
        if delivery_slot:
            return {
                'error': 'This delivery slot has reached its capacity. Choose another slot or date.' ,
                'error_type': 'limit_reached'}
        for line in order.order_line:
            if line.id == line_id:
                if slot_id:
                    line.slot_id = slot
                    line.delivery_slot_id = delivery_slot
        return {'success': 'Delivery slot updated.'}