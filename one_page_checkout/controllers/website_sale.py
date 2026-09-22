# -*- coding: utf-8 -*-
#############################################################################
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import json


class WebsiteSaleEcom(WebsiteSale):
    """
    Customized version of the website sale controller for e-commerce.
    This class is a subclass of `WebsiteSale` and provides additional
    customizations and overrides specific to e-commerce functionality on the
    website. It extends the base functionality of `WebsiteSale` to cater to the
    specific needs of an e-commerce website.

    Inherits:
        WebsiteSale: The base class for the website sale controller.
    Usage:
    1. Create an instance of `WebsiteSaleEcom` and customize it as needed.
    2. Use the instance to handle e-commerce functionality on your website.
    """

    def _get_address_values(self, **post):
        """
        This method overrides the default `address()` method of the
        `WebsiteSale` class to get additional context values related to the
        customer's address.

        :param post: A dictionary containing the form data submitted by the
        user.
        :type post: dict

        :return: A dictionary containing the updated q-context values related
        to the customer's address.
        :rtype: dict
        """
        res = super().shop_address(**post)

        if hasattr(res, 'qcontext'):
            return res.qcontext

        return {}

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'],
                auth="public", website=True, sitemap=False)
    def shop_address(self, **kw):
        """
        Renders the checkout address page for the current website sale order.
        If the request is a POST, updates the current order's delivery and
        invoice addresses with the provided data.

        If the current user is authenticated and the order's partner matches
        the authenticated user's partner, redirects to the payment page.

        :return: An HTTP response with the rendered checkout address page or a
        redirection to the login or payment page.
        :rtype: werkzeug.wrappers.Response
        """
        res = super().shop_address(**kw)
        if hasattr(res, 'qcontext'):
            order = res.qcontext.get('website_sale_order')
            if order:
                user = request.website.user_id.sudo()
                if order.partner_id.id == user.partner_id.id:
                    return request.redirect('/shop/payment')
        return res

    @http.route(['/shop/extra_info'], type='http', auth="public", website=True,
                sitemap=False)
    def extra_info(self):
        """
        Overwrites the existing extra_info function.
        Redirects the current request to the checkout payment page.

        :return: An HTTP response redirecting to the checkout payment page.
        :rtype: werkzeug.wrappers.Response
        """
        return request.redirect('/shop/payment')

    @http.route('/shop/payment', type='http', auth='public', website=True,
                sitemap=False)
    def shop_payment(self, **post):
        """
        Overwrites the existing shop_payment function.
        Removed the redirection if there is no address for user.
        This page proposes several payment means based on available
        payment.provider. State at this point :

         - a draft sales order with lines; otherwise, clean context / session
            and back to the shop
         - no transaction in context / session, or only a draft one, if the
            customer did go to a payment.provider webshop_paymentsite but
            closed the tab without paying / canceling
        """
        order = request.cart
        if not order:
            return request.redirect('/shop/cart')

        validation_error = {}
        submitted_checkout = {}

        if post.get('submitted'):
            submit_post = dict(post)
            # Standard shop_address_submit expects None for new addresses or valid partner_id
            if 'partner_id' in submit_post and str(submit_post['partner_id']) in ('0', '-1'):
                submit_post['partner_id'] = None

            res = self.shop_address_submit(**submit_post)

            res_data = ""
            if isinstance(res, str):
                res_data = res
            elif hasattr(res, 'data'):
                res_data = res.data.decode('utf-8')
            elif hasattr(res, 'flatten'):
                res_data = res.flatten()

            if res_data:
                feedback = json.loads(res_data)
                if feedback.get('invalid_fields') or feedback.get('messages'):
                    validation_error = {field: 'error' for field in feedback.get('invalid_fields', [])}
                    if feedback.get('messages'):
                        validation_error['error_message'] = feedback['messages']
                    submitted_checkout = submit_post
                elif feedback.get('redirectUrl'):
                    return request.redirect('/shop/payment')

        # Only force partner_id=-1 if it's an anonymous cart and we don't have errors to show
        # This allows the address form to show up for first-time guest checkouts.
        is_anonymous = order._is_anonymous_cart()
        if is_anonymous and not validation_error:
            post.update({'partner_id': -1})
        # Included /address values to the /payment and its template
        address_values = self._get_address_values(**post)
        render_values = self._get_shop_payment_values(order, **post)
        render_values['only_services'] = order and order.only_services or False

        render_values.update({
            'account_on_checkout': address_values.get('account_on_checkout'),
            'country_states': address_values.get('country_states', []),
            'is_public_user': is_anonymous if not validation_error else True,
            'only_services': address_values.get('only_services', order.only_services),
            'countries': address_values.get('countries', []),
            'country': address_values.get('country', []),
            'checkout': submitted_checkout or address_values.get('checkout', {}),
            'error': validation_error or address_values.get('error', {}),
            'mode': address_values.get('mode', ('new', 'billing')),
            'deliveries': order._get_delivery_methods().sudo(),
            'delivery_action_id': request.env.ref(
                'delivery.action_delivery_carrier_form'
            ).id,
            'sale_order_id': order.id,
            'partner_id': address_values.get('partner_id') or order.partner_id.id
        })

        if render_values.get('errors'):
            render_values.pop('payment_methods_sudo', '')
            render_values.pop('tokens_sudo', '')

        request.session['sale_last_order_id'] = order.id
        render_values.update(request.website._get_checkout_step_values())
        return request.render("website_sale.payment", render_values)
