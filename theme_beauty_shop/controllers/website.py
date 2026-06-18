# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
"""
Controller for handling website-related operations for the Beauty Shop theme,
specifically cart management.
"""
from odoo import http
from odoo.http import request


class BeautyShopSale(http.Controller):
    """
    Controller for managing shopping cart actions in the Beauty Shop theme.
    """

    @http.route(['/beauty/cart/update'], type='http', auth='public',
                methods=['POST'], website=True, csrf=True)
    def cart_add(self, product_id, add_qty=1, **kw):
        """
        Adds a product to the cart or updates the quantity of an existing
        product in the cart.
        """
        product_id = int(product_id)
        add_qty = float(add_qty)
        SaleOrder = request.env['sale.order'].sudo()
        SaleOrderLine = request.env['sale.order.line'].sudo()
        product = request.env['product.product'].sudo().browse(product_id)
        # Get or create the cart order
        sale_order_id = request.session.get('sale_order_id')
        order = SaleOrder.browse(sale_order_id).exists() if sale_order_id else None
        if not order or order.state != 'draft':
            order = SaleOrder.create({
                'partner_id': request.env.user.partner_id.id,
                'website_id': request.website.id,
                'company_id': request.website.company_id.id,
                'team_id': request.website.salesteam_id.id if request.website.salesteam_id else False,
            })
            request.session['sale_order_id'] = order.id
        # Check if product already in cart
        existing_line = SaleOrderLine.search([
            ('order_id', '=', order.id),
            ('product_id', '=', product_id),
        ], limit=1)
        if existing_line:
            existing_line.product_uom_qty += add_qty
        else:
            SaleOrderLine.create({
                'order_id': order.id,
                'product_id': product_id,
                'product_uom_qty': add_qty,
                'product_uom_id': product.uom_id.id,
                'price_unit': product.lst_price,
                'name': product.display_name,
            })
        return request.redirect('/shop/cart')

    @http.route(['/beauty/cart/clear'], type='http', auth='public', website=True)
    def cart_clear(self, **kw):
        """
        Clears the current user's shopping cart by removing all order lines.
        """
        sale_order_id = request.session.get('sale_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id).exists()
            if order and order.state == 'draft':
                order.order_line.sudo().unlink()
        return request.redirect('/shop/cart')
