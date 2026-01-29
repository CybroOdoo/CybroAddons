# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    """ updating the cart quantity"""

    @http.route(['/shop/multi_cart'], type='http', auth="public", website=True)
    def cart_popup_update(self, url_refferer='', **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        qty_total = 0
        if post.get('product_tmpl_id'):
            request.website.get_current_pricelist()
            request_order = request.website.sale_get_order(force_create=1)
            product_template = request.env['product.template'].sudo().search(
                [('id', '=', post.get('product_tmpl_id'))])
            qty_total = 0

            if product_template:
                quantity = 0
                for variant in product_template.product_variant_ids:
                    if post.get('quantity-%s' % variant.id):
                        quantity = float(post.get('quantity-%s' % variant.id))
                        if quantity >= 1:
                            request.website.sale_get_order(
                                force_create=1)._cart_update(
                                product_id=int(variant.id),
                                add_qty=float(quantity))
                        qty_total += quantity
        if qty_total > 0:
            if post.get('buy_now'):
                return request.redirect('/shop/payment')
            return request.redirect('/shop/cart')
        else:
            return request.redirect('/shop')
