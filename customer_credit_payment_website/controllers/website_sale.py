# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra K (odoo@cybrosys.com)
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
###############################################################################
from datetime import datetime
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleInherit(WebsiteSale):
    """Custom class inheriting from WebsiteSale to implement additional
    features."""

    @http.route(['/shop/cart'], type='http', auth="public", website=True,
                sitemap=False)
    def cart(self, **post):
        """
        Override of the controller for updating the product amount in the
        shopping cart.
        """
        order = request.website.sale_get_order(force_create=True)
        res_super = super(WebsiteSaleInherit, self).cart(**post)
        amount = post.get('amount')
        if amount:
            product_id = request.env.ref(
                'customer_credit_payment_website.credit_product_0').id
            order.update({
                'credit_amount_sale': amount,
                'order_line': [(5, 0, 0), (0, 0, {
                    'product_id': product_id,
                    'price_unit': amount,
                    'tax_id': False,
                })]
            })
        res_super.qcontext.update({
            'website_sale_order': order,
            'amount': amount,
        })
        return res_super

    @http.route(['/shop/confirm_order'], type='http', auth="public",
                website=True, sitemap=False)
    def confirm_order(self, **post):
        """ Override the function to update the amount for the credit amount
        that purchase from the website."""
        order = request.website.sale_get_order()
        if not order:
            return request.redirect('/shop')
        product_id = request.env.ref(
            'customer_credit_payment_website.credit_product_0').id
        redirection = self.checkout_redirection(
            order) or self.checkout_check_address(order)
        if redirection:
            return redirection
        order.order_line._compute_tax_id()
        request.session['sale_last_order_id'] = order.id
        request.website.sale_get_order(update_pricelist=True)
        extra_step = request.website.viewref('website_sale.extra_info')
        if extra_step.active:
            return request.redirect("/shop/extra_info")
        if order.credit_amount_sale:
            order.update({
                'order_line': [(5, 0, 0), (0, 0, {
                    'product_id': product_id,
                    'price_unit': order.credit_amount_sale,
                })]
            })
        return request.redirect("/shop/payment")

    @http.route(['/shop/confirmation'], type='http', auth="public",
                website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        """ End of checkout process controller. Confirmation is basically seeing
        the status of a sale.order. """
        sale_order_id = request.session.get('sale_last_order_id')
        if not sale_order_id:
            return request.redirect('/shop')
        order = request.env['sale.order'].sudo().browse(sale_order_id)
        user_id = request.env.user
        partner = user_id.partner_id
        order_amount_total = order.amount_total
        payment_transaction = request.env['payment.transaction'].search(
            [('reference', '=', order.name)])
        payment_transaction_id = payment_transaction.provider_id
        credit_product_id = request.env.ref(
            'customer_credit_payment_website.credit_product_0').id
        credit_payment_provider_id = request.env.ref(
            'customer_credit_payment_website.payment_provider_credit').id
        has_credit_product = any(
            line.product_id.id == credit_product_id for line in
            order.order_line)
        if (has_credit_product and
                payment_transaction_id.id != credit_payment_provider_id):
            request.env['credit.amount'].create({
                'customer_id': partner.id,
                'amount': order_amount_total
            })
        elif (not has_credit_product and
              payment_transaction_id.id == credit_payment_provider_id):
            if order.amount_total < partner.credit_amount:
                credit_detail = request.env['credit.details'].search(
                    [('customer_id', '=', partner.id)])
                credit_detail.write({
                    'debit_details_ids': [(0, 0, {
                        'debit_amount': -order_amount_total,
                        'approve_date': datetime.now(),
                        'updated_amount':
                            -order_amount_total + credit_detail.debit_amount,
                        'previous_debit_amount': credit_detail.debit_amount,
                    })]
                })
            elif order.amount_total > partner.credit_amount:
                if not partner.allow_credit_amount:
                    return request.render(
                        'customer_credit_payment_website.credit_error_details',
                        {'name': order.name})
                else:
                    credit_detail = request.env['credit.details'].search(
                        [('customer_id', '=', partner.id)])
                    credit_detail.write({
                        'debit_details_ids': [(0, 0, {
                            'debit_amount': -order_amount_total,
                            'approve_date': datetime.now(),
                            'previous_debit_amount': credit_detail.debit_amount,
                            'updated_amount':
                            -order_amount_total + credit_detail.debit_amount,
                        })]
                    })
        values = self._prepare_shop_payment_confirmation_values(order)
        return request.render("website_sale.confirmation", values)
