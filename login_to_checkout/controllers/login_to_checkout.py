# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
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
###############################################################################
from odoo.http import request
from odoo import http
from odoo.addons.payment.controllers import portal as payment_portal


class WebsiteSaleForm(payment_portal.PaymentPortal):

    @http.route('/shop/payment', type='http', auth='public', website=True,
                sitemap=False)
    def shop_payment(self, **post):
        """ Payment step. This page proposes several payment means based on available
        payment.provider. State at this point :

        - a draft sales order with lines; otherwise, clean context/session and
          back to the shop.
        - no transaction in context/session, or only a draft one, if the customer
          did go to a payment.provider website but closed the tab without
          paying/canceling.
        """
        if request.env.user._is_public():
            return request.redirect('/web/login')
        else:
            order_sudo = request.website.sale_get_order()
            if redirection := self._check_cart_and_addresses(order_sudo):
                return redirection
            render_values = self._get_shop_payment_values(order_sudo, **post)
            render_values[
                'only_services'] = order_sudo and order_sudo.only_services
            if render_values['errors']:
                render_values.pop('payment_methods_sudo', '')
                render_values.pop('tokens_sudo', '')
            return request.render("website_sale.payment", render_values)
