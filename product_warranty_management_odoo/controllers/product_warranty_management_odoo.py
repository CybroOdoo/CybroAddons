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


class WarrantyClaimController(http.Controller):
    """Website warranty claim form of the logged-in customer."""

    def _get_warranty_orders(self):
        """Return the confirmed warranty orders of the current customer."""
        partner = request.env.user.partner_id.commercial_partner_id
        return request.env['sale.order'].sudo().search([
            ('partner_id', 'child_of', partner.id),
            ('state', '=', 'sale'),
            ('is_warranty_check', '=', True),
        ])

    def _get_warranty_lines(self, order_id):
        """Return the warranty lines of an order of the current customer."""
        order = self._get_warranty_orders().filtered(
            lambda rec: rec.id == order_id)
        return order.order_line.filtered('is_warranty_available')

    def _render_claim_form(self, error=None, values=None):
        """Render the claim form with an optional error message."""
        return request.render(
            'product_warranty_management_odoo.warranty_claim_page', {
                'customer': request.env.user.partner_id,
                'sale_orders': self._get_warranty_orders(),
                'error': error,
                'values': values or {},
            })

    @http.route('/warranty', type='http', auth='user', website=True)
    def warranty_claim(self):
        """Show the warranty claim form."""
        return self._render_claim_form()

    @http.route('/warranty/products', type='jsonrpc', auth='user',
                website=True)
    def warranty_products(self, order_id):
        """Return the warranty products of the selected sale order."""
        products = self._get_warranty_lines(int(order_id)).product_id
        return [{'id': product.id, 'name': product.display_name}
                for product in products]

    @http.route('/warranty/claim/submit', type='http', auth='user',
                website=True, methods=['POST'])
    def warranty_claim_submit(self, **post):
        """Validate the posted claim and create it."""
        try:
            order_id = int(post.get('sale_order_id') or 0)
            product_id = int(post.get('product_id') or 0)
        except ValueError:
            order_id = product_id = 0
        lines = self._get_warranty_lines(order_id)
        if not lines or product_id not in lines.product_id.ids:
            return self._render_claim_form(
                error=request.env._('Select a sale order and a product '
                                    'that has a warranty.'),
                values=post)
        claim_model = request.env['warranty.claim'].sudo()
        if claim_model.search_count([('sale_order_id', '=', order_id),
                                     ('product_id', '=', product_id),
                                     ('state', '!=', 'rejected')]):
            return self._render_claim_form(
                error=request.env._('A warranty claim already exists for '
                                    'this product on this sale order.'),
                values=post)
        claim_model.create({
            'customer_id': request.env.user.partner_id.id,
            'sale_order_id': order_id,
            'product_id': product_id,
            'description': post.get('description'),
        })
        return request.render(
            'product_warranty_management_odoo.claim_thanks_view')
