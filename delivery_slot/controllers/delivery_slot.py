# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Manasa T P (odoo@cybrosys.com)
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
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    """Extends the WebsiteSale controller to add delivery slot functionality."""

    def _get_delivery_slot_error(self, delivery_slot):
        """Return a website-friendly error when a slot cannot be selected."""
        if delivery_slot and not delivery_slot.active:
            return {
                'error': 'This delivery slot is not available.',
                'error_type': 'slot_unavailable'}
        if delivery_slot and delivery_slot.remaining_slots <= 0:
            return {
                'error': 'This delivery slot has reached its capacity. Choose another slot or date.',
                'error_type': 'limit_reached'}
        return False

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

    @http.route(['/shop/cart/update_json'], type='json', auth="public",
                methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, **kw):
        """Passing delivery date and slot values"""
        val = super().cart_update_json(**kw)
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

    @http.route(['/shop/cart/get_option'], type='json', auth="public",
                website=True)
    def get_option(self, **kw):
        """Called when changing the slot timing ie office hours or home hours
        returns the option chosen"""
        option = kw.get('selected_option')
        slot_filtered = request.env['slot.time'].search([]).filtered(
            lambda l: l.slot_type == option)
        options = [[slot.id, slot.name] for slot in slot_filtered]
        return options

    @http.route(['/shop/cart/set_delivery_date'], type='json', auth="public",
                website=True)
    def set_delivery_date(self, **kwargs):
        """Sets the delivery date for each order line of sale order created"""
        order = request.website.sale_get_order()
        date = kwargs.get('delivery_date')
        line_id = int(kwargs.get('line_id'))
        line = order.order_line.filtered(lambda order_line: order_line.id == line_id)
        if not line:
            return {'error': 'Order line not found.',
                    'error_type': 'validation_error'}
        try:
            line.write({
                'delivery_date': date,
                'slot_id': False,
                'delivery_slot_id': False,
            })
        except ValidationError as error:
            return {
                'error': error.args[0],
                'error_type': 'validation_error'}
        return {'success': 'Delivery date updated.'}

    @http.route(['/shop/cart/get_available_slots'], type='json', auth="public",
                website=True)
    def get_available_slots(self, **kwargs):
        """Returns slots that have not yet reached their delivery limit for the given date.
        Optionally filters by slot_type (home/office)."""
        date = kwargs.get('date')
        selected_option = kwargs.get('selected_option')
        domain = []
        if selected_option:
            domain.append(('slot_type', '=', selected_option))
        all_slots = request.env['slot.time'].search(domain)
        options = []
        for slot in all_slots:
            if date:
                delivery_slot = request.env['delivery.slot'].with_context(
                    active_test=False).search([
                    ('slot_id', '=', slot.id),
                    ('delivery_date', '=', date),
                ], limit=1)
                # If no delivery slot record exists yet, it means no orders yet — it's available
                if (delivery_slot and
                        (not delivery_slot.active or
                         delivery_slot.remaining_slots <= 0)):
                    continue
            options.append([slot.id, slot.name])
        return options


    @http.route(['/shop/cart/set_delivery_slot'], type='json', auth="public",
                website=True)
    def set_delivery_slot(self, **kwargs):
        """Sets the delivery slots for each order line of sale order created"""
        order = request.website.sale_get_order()
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
        delivery_slot = request.env['delivery.slot'].with_context(
            active_test=False).search([
            ('slot_id', '=', slot_id),
            ('delivery_date', '=', delivery_date),
        ], limit=1)
        error = self._get_delivery_slot_error(delivery_slot)
        if error:
            return error
        for line in order.order_line:
            if line.id == line_id:
                if slot_id:
                    try:
                        line.write({
                            'slot_id': slot.id,
                            'delivery_slot_id': delivery_slot.id,
                        })
                    except ValidationError as error:
                        return {
                            'error': error.args[0],
                            'error_type': 'validation_error'}
        return {'success': 'Delivery slot updated.'}
