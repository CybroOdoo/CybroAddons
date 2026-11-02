# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Abbas P (odoo@cybrosys.com)
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
################################################################################
from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools import float_compare


class SaleReturnController(http.Controller):
    """Website routes for raising a return from the sale order portal page"""

    def _return_error(self, order, error):
        """Send the customer back to the order page with an error code"""
        return request.redirect(
            order.get_portal_url(query_string='&return_error=%s' % error))

    @http.route('/sale_return', type='http', methods=['POST'], auth='user',
                website=True)
    def sale_return(self, **kwargs):
        """Create a return order for a product of the customer's order"""
        try:
            order = request.env['sale.order'].browse(
                int(kwargs.get('order_id'))).exists()
            if not order:
                raise MissingError(request.env._("Order not found."))
            order.check_access('read')
        except (AccessError, MissingError, TypeError, ValueError):
            return request.redirect('/my')
        # The customer can read their own order but not its products or
        # deliveries, so these lookups run as superuser, limited to the
        # order the access check above has just cleared.
        order_sudo = order.sudo()
        try:
            product = order_sudo.order_line.product_id.filtered(
                lambda p: p.id == int(kwargs.get('product')))
        except (TypeError, ValueError):
            product = order_sudo.env['product.product']
        if not product:
            return self._return_error(order, 'product')
        try:
            qty = float(kwargs.get('qty'))
        except (TypeError, ValueError):
            return self._return_error(order, 'qty')
        precision = request.env['decimal.precision'].precision_get(
            'Product Unit')
        returnable = request.env['sale.return']._get_returnable_qty(
            order_sudo, product)
        if (float_compare(qty, 0.0, precision_digits=precision) <= 0
                or float_compare(qty, returnable,
                                 precision_digits=precision) > 0):
            return self._return_error(order, 'qty')
        moves = order_sudo._get_return_source_pickings().move_ids.filtered(
            lambda move: move.product_id == product and move.state == 'done')
        if not moves:
            return self._return_error(order, 'delivery')
        picking = moves.sorted('product_uom_qty', reverse=True)[0].picking_id
        sale_return = request.env['sale.return'].create({
            'partner_id': order.partner_id.id,
            'sale_order_id': order.id,
            'product_id': product.id,
            'quantity': qty,
            'reason': kwargs.get('reason'),
            'user_id': order_sudo.user_id.id,
        })
        picking.write({
            'return_order_id': sale_return.id,
            'return_order_picking': False,
        })
        return request.redirect('/my/request-thank-you')

    @http.route('/my/request-thank-you', type='http', auth='user',
                website=True)
    def return_request_thanks(self):
        """Confirmation page shown after a return request"""
        return request.render(
            'website_return_management.customers_request_thank_page')
