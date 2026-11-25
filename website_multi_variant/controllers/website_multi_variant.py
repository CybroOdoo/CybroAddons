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
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteVariantSale(WebsiteSale):
    """WebsiteSale class is inherited to add the
    functionality to add the variants if selected."""

    @http.route('/shop/cart/multi', type='http', auth="public", website=True, sitemap=False)
    def cart_update_multi(self, **post):
        """This controller is triggered when the multi-variant form is submitted
        and will update the cart and redirect to payment if 'Buy Now' is selected,
        otherwise redirect to cart."""
        if not request.env.website.has_ecommerce_access():
            return request.redirect('/web/login')

        if post.get('product_tmpl_id'):
            try:
                tmpl_id = int(post.get('product_tmpl_id'))
                product_template = request.env['product.template'].browse(tmpl_id).exists()
                variants = product_template.product_variant_ids if product_template else []
            except (ValueError, TypeError, AccessError):
                product_template = False
                variants = []

            if product_template and variants:
                variants_to_add = []
                for variant in variants:
                    try:
                        if not variant._is_add_to_cart_allowed():
                            continue
                    except AccessError:
                        continue
                    qty_raw = post.get(f'quantity-{variant.id}')
                    if qty_raw:
                        try:
                            quantity = float(qty_raw)
                        except (ValueError, TypeError):
                            quantity = 0.0
                        if quantity >= 1:
                            variants_to_add.append((variant, int(quantity)))

                if variants_to_add:
                    order_sudo = request.cart or request.env.website._create_cart()
                    order_sudo._check_not_partially_paid()
                    for variant, qty in variants_to_add:
                        order_sudo.with_context(skip_cart_verification=True)._cart_add(
                            product_id=variant.id,
                            quantity=qty,
                        )
                    order_sudo._verify_cart_after_update()
                    request.session['website_sale_cart_quantity'] = order_sudo.cart_quantity

        if post.get('buy_now'):
            return request.redirect('/shop/payment')
        return request.redirect('/shop/cart')
