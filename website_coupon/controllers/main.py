# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class WebsiteCoupon(http.Controller):

    @http.route(['/shop/cart'], type='http', auth="public", website=True)
    def cart(self, **post):
        """ This function is overwritten because we need to pass the value
        'coupon_not_available' to the template, in order to show the error
        message to the user that, 'this coupon is not available'.
        """

        order = request.website.sale_get_order()
        if order:
            from_currency = order.company_id.currency_id
            to_currency = order.pricelist_id.currency_id
            compute_currency = lambda price: from_currency.compute(
                price, to_currency)
        else:
            compute_currency = lambda price: price

        values = {
            'website_sale_order': order,
            'compute_currency': compute_currency,
            'suggested_products': [],
        }
        if order:
            _order = order
            if not request.env.context.get('pricelist'):
                _order = order.with_context(pricelist=order.pricelist_id.id)
            values['suggested_products'] = _order._cart_accessories()

        if post.get('type') == 'popover':
            # force no-cache so IE11 doesn't cache this XHR
            return request.render("website_sale.cart_popover", values,
                                  headers={'Cache-Control': 'no-cache'})

        if post.get('code_not_available'):
            values['code_not_available'] = post.get('code_not_available')
        elif post.get('coupon_not_available'):
            values['coupon_not_available'] = post.get('coupon_not_available')
        return request.render("website_sale.cart", values)

    @http.route(['/shop/gift_coupon'],
                type='http', auth="public", website=True)
    def gift_coupon(self, promo_voucher, **post):
        """ This function will be executed when we click the apply button of
        the voucher code in the website. It will verify the validity and
        availability of that coupon. If it can be applied, the coupon will be
        applied and coupon balance will also be updated.
        """

        coupon = request.env['gift.coupon'].sudo().search(
            [('code', '=', promo_voucher)])
        base_url = '/shop/cart'

        if not coupon or not coupon.is_valid(request.env.user.partner_id):
            return request.redirect(base_url + '?coupon_not_available=1')

        order = request.website.sale_get_order(force_create=1)
        gift_product = request.env['product.product'].sudo().search(
            [('name', '=', 'Gift Coupon')], limit=1)

        # Make sure the gift product is not already in current order
        if any(True for line in order.order_line
               if line.product_id == gift_product):
            return request.redirect(base_url + '?coupon_not_available=2')

        used, amount = coupon.consume_coupon(order)
        if used:
            gift_product.product_tmpl_id.list_price = -amount
            order._cart_update(product_id=gift_product.id, set_qty=used)
            return request.redirect(base_url)
        else:
            return request.redirect(base_url + '?coupon_not_available=1')
