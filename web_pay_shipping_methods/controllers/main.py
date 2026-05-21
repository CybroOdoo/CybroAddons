# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fansa Jabeen A (odoo@cybrosys.com)
#
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.addons.payment.controllers import portal as payment_portal

from odoo.http import route, request
from odoo.tools import str2bool


class WebsiteSale(payment_portal.PaymentPortal):
    @route('/shop/payment', type='http', auth='public', website=True, sitemap=False)
    def shop_payment(self, try_skip_step=None, **post):
        """ Payment step. This page proposes several payment means based on available
        payment.provider. State at this point :

         - a draft sales order with lines; otherwise, clean context / session and
           back to the shop
         - no transaction in context / session, or only a draft one, if the customer
           did go to a payment.provider website but closed the tab without
           paying / canceling
        """
        try_skip_step = str2bool(try_skip_step or 'false')
        order_sudo = request.cart

        checkout_page_values = self._prepare_checkout_page_values(order_sudo, **post)

        if redirection := self._check_cart_and_addresses(order_sudo):
            return redirection

        render_values = self._get_shop_payment_values(order_sudo, **post)
        render_values['only_services'] = order_sudo and order_sudo.only_services

        can_skip_delivery = True  # Delivery is only needed for deliverable products.
        if order_sudo._has_deliverable_products():
            available_dms = order_sudo._get_delivery_methods()
            checkout_page_values['delivery_methods'] = available_dms
            if delivery_method := order_sudo._get_preferred_delivery_method(available_dms):
                rate = delivery_method.rate_shipment(order_sudo)
                render_values['delivery_methods'] = checkout_page_values['delivery_methods']
                if (
                    not order_sudo.carrier_id
                    or not rate.get('success')
                    or order_sudo.amount_delivery != rate['price']
                ):
                    order_sudo._set_delivery_method(delivery_method, rate=rate)
            can_skip_delivery = not order_sudo._has_deliverable_products()

        if try_skip_step and can_skip_delivery:
            return request.redirect('/shop/confirm_order')

        if render_values['errors']:
            render_values.pop('payment_methods_sudo', '')
            render_values.pop('tokens_sudo', '')


        allowed_steps_domain = [('website_id', '=', request.website.id)]

        current_step = request.env['website.checkout.step'].sudo().search(
            allowed_steps_domain + [('step_href', '=', '/shop/payment')],
            limit=1
        )

        next_step = current_step._get_next_checkout_step(allowed_steps_domain)
        previous_step = current_step._get_previous_checkout_step(
            allowed_steps_domain)

        render_values.update({
            'next_website_checkout_step': next_step,
            'previous_website_checkout_step': previous_step,
            'checkout_step': 'payment',
            'current_website_checkout_step_href': '/shop/payment',
        })

        return request.render("website_sale.payment", render_values)
