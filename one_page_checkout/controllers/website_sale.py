# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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
        result = super(WebsiteSaleEcom, self).address(**post).qcontext
        return result

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'],
                auth="public", website=True, sitemap=False)
    def address(self, **kw):
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

        res = super(WebsiteSaleEcom, self).address(**kw)
        order = request.website.sale_get_order()
        render_values = self._get_shop_payment_values(order, **kw)
        render_values.update({
            'is_public_user': request.website.is_public_user(),
            'is_address': False})
        request.render("website_sale.address", render_values)
        order = res.qcontext.get('website_sale_order')
        if order:
            user = request.website.user_id.sudo()
            if order.partner_id.id == user.partner_id.id:
                return request.redirect('/shop/payment')
            else:
                return res
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
            customer did go to a 'payment.provider' webshop_payment site but
            closed the tab without paying / canceling
        """
        order = request.website.sale_get_order()
        render_values = self._get_shop_payment_values(order, **post)
        render_values['only_services'] = order and order.only_services or False
        address_values = self._get_address_values(**post)
        # Included /address values to the /payment and its template
        render_values.update({
            'country_states': address_values.get('country_states', []),
            'only_services': address_values.get('only_services', False),
            'countries': address_values.get('countries', []),
            'country': address_values.get('country', []),
            'checkout': address_values.get('checkout', []),
            'error': address_values.get('error', {}),
            'mode': address_values.get('mode', 'shipping'),
            'add': True if address_values.get('response_template') is None else False,
        })
        if render_values['errors']:
            render_values.pop('providers', '')
            render_values.pop('tokens', '')
        return request.render("website_sale.payment", render_values)
