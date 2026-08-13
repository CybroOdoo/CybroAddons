# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jigin K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License (AGPL) for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    (AGPL) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import http
from odoo.http import request, route
from odoo.addons.website_sale.controllers.cart import Cart


class WebsiteCountry(http.Controller):
    """
        This controller used to pass the selected country to the corresponding
        template
    """
    @http.route('/website/countries', type='jsonrpc', auth="user", website=True)
    def website_countries(self, country_id):
        """
            This function used to search the country id, and it renders the
            details of the selected country in to the template.
        """
        country_id = request.env['res.country'].browse(int(country_id))
        website_id = request.env['website'].browse(request.website.id)
        website_id.default_country_id = country_id.id
        response = http.Response(
            template='website_restrict_country.country_selection',
            qcontext={'country': country_id,
                      'countries': website_id.country_ids})
        return response.render()


class WebsiteSaleCountryRestriction(Cart):
    """
        Extends the cart controller so the payment area is re-rendered on every
        cart update. The default '/shop/cart/update' route only refreshes the
        cart lines and totals, which leaves a stale "Pay" button when removing a
        line changes whether the cart is fully restricted to the selected
        country.
    """
    @route()
    def update_cart(self, *args, **kwargs):
        """ Add the re-rendered cart summary (which holds the payment buttons)
            to the response so the frontend updates it without a page reload. """
        values = super().update_cart(*args, **kwargs)
        order_sudo = request.cart
        if order_sudo:
            values['website_sale.shorter_cart_summary'] = request.env[
                'ir.ui.view']._render_template(
                'website_sale.shorter_cart_summary', {
                    'website_sale_order': order_sudo,
                    'show_shorter_cart_summary': True,
                    **self._get_express_shop_payment_values(order_sudo),
                    **request.website._get_checkout_step_values(),
                })
        return values
