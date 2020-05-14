# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import fields, http, tools, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteCoupon(WebsiteSale):

    @http.route(['/shop/cart'], type='http', auth="public", website=True)
    def cart(self, access_token=None, revive='', **post):

        order = request.website.sale_get_order()
        if order and order.state != 'draft':
            request.session['sale_order_id'] = None
            order = request.website.sale_get_order()
        values = {}

        if order:
            from_currency = order.company_id.currency_id
            to_currency = order.pricelist_id.currency_id
            compute_currency = lambda price: from_currency._convert(
                price, to_currency, request.env.user.company_id, fields.Date.today())
        else:
            compute_currency = lambda price: price

        values.update({
            'website_sale_order': order,
            'compute_currency': compute_currency,
            'date': fields.Date.today(),
            'suggested_products': [],
        })
        if order:
            _order = order
            if not request.env.context.get('pricelist'):
                _order = order.with_context(pricelist=order.pricelist_id.id)
            values['suggested_products'] = _order._cart_accessories()

        if post.get('type') == 'popover':
            return request.render("website_sale.cart_popover", values, headers={'Cache-Control': 'no-cache'})
        if post.get('code_not_available'):
            values['code_not_available'] = post.get('code_not_available')
        elif post.get('coupon_not_available'):
            values['coupon_not_available'] = post.get('coupon_not_available')

        return request.render("website_sale.cart", values)

    @http.route(['/shop/gift_coupon'], type='http', auth="public", website=True)
    def gift_coupon(self, promo_voucher, **post):
        """This function will be executed when we click the apply button of the voucher code in the website.
        It will verify the validity and availability of that coupon. If it can be applied, the coupon  will be applied
        and coupon balance will also be updated"""

        curr_user = request.env.user
        coupon = request.env['gift.coupon'].sudo().search([('code', '=', promo_voucher)], limit=1)
        flag = True
        if coupon and coupon.total_avail > 0:
            applied_coupons = request.env['partner.coupon'].sudo().search([('coupon', '=', promo_voucher),
                                                                           (
                                                                           'partner_id', '=', curr_user.partner_id.id)],
                                                                          limit=1)

            # checking voucher date and limit for each user for this coupon---------------------
            if coupon.partner_id:
                if curr_user.partner_id.id != coupon.partner_id.id:
                    flag = False
            today = datetime.now().date()
            if flag and applied_coupons.number < coupon.limit and today <= coupon.voucher.expiry_date:
                # checking coupon validity ---------------------------
                #    checking date of coupon ------------
                if coupon.start_date and coupon.end_date:
                    if today < coupon.start_date or today > coupon.end_date:
                        flag = False
                elif coupon.start_date:
                    if today < coupon.start_date:
                        flag = False
                elif coupon.end_date:
                    if today > coupon.end_date:
                        flag = False
            else:
                flag = False
        else:
            flag = False
        if flag:
            voucher_type = coupon.voucher.voucher_type
            voucher_val = coupon.voucher_val
            type = coupon.type
            coupon_product = request.env['product.product'].sudo().search([('default_code', '=', 'gift_coupon')], limit=1)
            if coupon_product:
                order = request.website.sale_get_order(force_create=1)
                flag_product = False
                for line in order.order_line:
                    if line.product_id.default_code == 'gift_coupon':
                        flag = False
                        break
                if flag and order.order_line:
                    if voucher_type == 'product':
                        # the voucher type is product ----------------------------
                        categ_id = coupon.voucher.product_id
                        for line in order.order_line:
                            if line.product_id.name == categ_id.name:
                                flag_product = True
                    elif voucher_type == 'category':
                        # the voucher type is category ----------------------------
                        product_id = coupon.voucher.product_categ
                        for line in order.order_line:
                            if line.product_id.categ_id.name == product_id.name:
                                flag_product = True
                    elif voucher_type == 'all':
                        # the voucher is applicable to all products ----------------------------
                        flag_product = True
                    if flag_product:
                        # the voucher is applicable --------------------------------------
                        if type == 'fixed':
                            # coupon type is 'fixed'--------------------------------------
                            if voucher_val < order.amount_total:
                                coupon_product.product_tmpl_id.write({'list_price': -voucher_val})

                            else:
                                return request.redirect("/shop/cart?coupon_not_available=3")
                        elif type == 'percentage':
                            # coupon type is percentage -------------------------------------
                            amount_final = 0
                            if voucher_type == 'product':
                                for line in order.order_line:
                                    if line.product_id.name == categ_id.name:
                                        amount_final = (voucher_val / 100) * line.price_total
                                        break
                            elif voucher_type == 'category':
                                for line in order.order_line:
                                    if line.product_id.categ_id.name == product_id.name:
                                        amount_final += (voucher_val / 100) * line.price_total
                            elif voucher_type == 'all':
                                amount_final = (voucher_val / 100) * order.amount_total
                            coupon_product.product_tmpl_id.write({'list_price': -amount_final})
                        order._cart_update(product_id=coupon_product.id, set_qty=1, add_qty=1)
                        order = request.website.sale_get_order()
                        order.update({'coupon_id': promo_voucher})

                        # updating coupon balance--------------
                        # creating a record for this partner, i.e he is used this coupon once-----------
                    else:
                        return request.redirect("/shop/cart?coupon_not_available=1")
                else:
                    return request.redirect("/shop/cart?coupon_not_available=2")
        else:

            return request.redirect("/shop/cart?coupon_not_available=1")

        return request.redirect("/shop/cart")

    @http.route(['/shop/payment'], type='http', auth="public", website=True, sitemap=False)
    def payment(self, **post):
        """ Payment step. This page proposes several payment means based on available
        payment.acquirer. State at this point :

         - a draft sales order with lines; otherwise, clean context / session and
           back to the shop
         - no transaction in context / session, or only a draft one, if the customer
           did go to a payment.acquirer website but closed the tab without
           paying / canceling
        """

        order = request.website.sale_get_order()
        curr_user = request.env.user
        sales_order = request.env['sale.order.line'].sudo().search([('order_id', '=', order.id)])
        applied_coupons = request.env['partner.coupon'].sudo().search([('coupon', '=', order.coupon_id),
                                                                       ('partner_id', '=', curr_user.partner_id.id)],
                                                                      limit=1)
        coupon = request.env['gift.coupon'].sudo().search([('code', '=', order.coupon_id)], limit=1)

        products = []
        for data in sales_order:
            products.append(data.name)
        if 'Gift Coupon' in products:
            total = coupon.total_avail - 1
            coupon.write({'total_avail': total})
        if not applied_coupons:
            curr_user.partner_id.write(
                {'applied_coupon': [(0, 0, {'partner_id': curr_user.partner_id.id,
                                            'coupon': coupon.code,
                                            'number': 1})]})
        else:
            applied_coupons.write({'number': applied_coupons.number + 1})

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        render_values = self._get_shop_payment_values(order, **post)
        render_values['only_services'] = order and order.only_services or False

        if render_values['errors']:
            render_values.pop('acquirers', '')
            render_values.pop('tokens', '')

        return request.render("website_sale.payment", render_values)
