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
"""
This module provides the route /final/customer_rating to capture
comments and ratings on the website confirmation page.
"""
from odoo import http
from odoo.http import request


class CustomerRatingAndReview(http.Controller):
    """ Controller for handling customer comments and ratings from the website. """

    @http.route('/final/customer_rating', type='http', auth="public",
                methods=['POST'], website=True, csrf=True, sitemap=False)
    def customer_order_rating(self, **kw):
        """ Fetch and save customer comment and rating for the confirmed sale order. """
        is_enabled = request.env['ir.config_parameter'].sudo().get_bool(
            'customer_order_comment.comment_configuration'
        )
        if not is_enabled:
            return request.redirect('/shop/confirmation')

        order_id_val = kw.get('order_id')
        if not order_id_val:
            return request.redirect('/shop/confirmation')

        try:
            order_id = int(order_id_val)
        except (ValueError, TypeError):
            return request.redirect('/shop/confirmation')

        order = request.env['sale.order'].sudo().browse(order_id).exists()
        if not order:
            return request.redirect('/shop/confirmation')

        session_order_id = request.session.get('sale_last_order_id')
        is_session_order = session_order_id and session_order_id == order.id
        is_owner = not request.env.user._is_public() and order.partner_id == request.env.user.partner_id
        has_token = bool(kw.get('access_token') and kw.get('access_token') == order.access_token)

        if not (is_session_order or is_owner or has_token):
            return request.redirect('/shop/confirmation')

        vals = {}
        if 'comment' in kw and kw['comment']:
            vals['comment'] = str(kw['comment']).strip()

        rate_val = kw.get('rate_value')
        if rate_val is not None:
            rate_str = str(rate_val).strip()
            valid_keys = dict(order._fields['rating'].selection)
            if rate_str in valid_keys:
                vals['rating'] = rate_str

        if vals:
            order.write(vals)

        return request.redirect('/shop/confirmation')

