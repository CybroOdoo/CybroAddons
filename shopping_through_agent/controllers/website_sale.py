# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.sale.controllers import portal as sale_portal
from odoo.addons.website_sale.controllers import main as website_sale_main
from odoo.addons.website_sale.controllers import payment as website_sale_payment
from odoo.http import request, route


class WebsiteSale(website_sale_main.WebsiteSale):
    """Class to inherit the functions in the website sale"""

    @route()
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
        """Function to inherit shop and to set the posted value in the
        website session."""
        res = super().shop(page, category, search, min_price,
                           max_price, ppg, **post)
        order = request.website._create_cart()
        if 'post_values' in request.session:
            stored_post_values = request.session['post_values']
            if stored_post_values != post and post:
                order.unlink()
        if post:
            request.session['post_values'] = post
        return res


    def _get_shop_payment_values(self, order, **kwargs):
        """Function to update the sale order details created from website"""
        res = super()._get_shop_payment_values(order, **kwargs)
        if 'post_values' in request.session:
            post_values = request.session['post_values']
            if post_values:
                customer_id = post_values.get('customer')
                if customer_id:
                    customer = request.env['res.partner'].browse(
                        int(customer_id))
                    website_sale_order = res.get('website_sale_order', {})
                    website_sale_order.update({
                        'partner_id': customer.id,
                        'partner_invoice_id': customer.id,
                        'partner_shipping_id': customer.id,
                        'agent_id': request.env.user.partner_id.id
                        if request.env.user.partner_id.is_agent else False,
                    })
                    res.update({
                        'partner': customer,
                        'partner_id': customer.id,
                        'website_sale_order': website_sale_order,
                    })
        return res

    def _prepare_shop_payment_confirmation_values(self, order):
        """
        This method is called in the payment process route in order to
        prepare the dict containing the values to be rendered by the
        confirmation template.
        """
        res = super()._prepare_shop_payment_confirmation_values(order)
        if 'post_values' in request.session:
            post_values = request.session['post_values']
            if post_values:
                customer_id = post_values.get('customer')
                if customer_id:
                    customer = request.env['res.partner'].browse(
                        int(customer_id))
                    order.update({
                        'partner_id': customer.id,
                        'partner_invoice_id': customer.id,
                        'partner_shipping_id': customer.id,
                        'agent_id': request.env.user.partner_id.id
                    })
        return res

    def checkout_values(self, order, **kw):
        """Updating the billing and shipping address based on customer"""
        res = super().checkout_values(order, **kw)
        if 'post_values' in request.session:
            post_values = request.session['post_values']
            if post_values:
                customer_id = post_values.get('customer')
                if customer_id:
                    customer = request.env['res.partner'].browse(
                        int(customer_id))
                    res.update({
                        'shippings': customer,
                        'billings': customer,
                    })
        return res

    @route()
    def shop_payment_confirmation(self, **post):
        """Function to remove the values of post_values from the session."""
        res = super().shop_payment_confirmation(**post)
        request.session['post_values'] = {}
        return res


class PaymentPortal(website_sale_payment.PaymentPortal):
    """Class to inherit the function to change the details of the
    transactions."""

    @route()
    def shop_payment_transaction(self, order_id, access_token, **kwargs):
        """Function to change the order details for delivery and invoice"""
        order = request.env['sale.order'].sudo().browse(int(order_id))
        if 'post_values' in request.session:
            post_values = request.session['post_values']
            if post_values:
                customer_id = post_values.get('customer')
                if customer_id:
                    customer = request.env['res.partner'].browse(
                        int(customer_id))
                    order.write({
                        'partner_id': customer.id,
                        'partner_invoice_id': customer.id,
                        'partner_shipping_id': customer.id,
                        'agent_id': request.env.user.partner_id.id
                    })
                    if not order.only_services and not order.carrier_id:
                        delivery_methods = order._get_delivery_methods()
                        if delivery_methods:
                            delivery_method = order._get_preferred_delivery_method(
                                delivery_methods)
                            order._set_delivery_method(delivery_method)

        return super().shop_payment_transaction(order_id, access_token, **kwargs)


class CustomerPortal(sale_portal.CustomerPortal):
    """Override portal order/quotation domain to include orders placed by the
    logged-in agent on behalf of their customers."""

    def _prepare_orders_domain(self, partner):
        """Extend the domain so that agents also see orders they created on
        behalf of customers (i.e. where agent_id = the current partner)."""
        domain = super()._prepare_orders_domain(partner)
        if partner.is_agent:
            return [
                '|',
                ('partner_id', 'child_of', [partner.commercial_partner_id.id]),
                ('agent_id', '=', partner.id),
                ('state', '=', 'sale'),
            ]
        return domain

    def _prepare_quotations_domain(self, partner):
        """Extend the domain so that agents also see quotations they created on
        behalf of customers (i.e. where agent_id = the current partner)."""
        domain = super()._prepare_quotations_domain(partner)
        if partner.is_agent:
            return [
                '|',
                ('partner_id', 'child_of', [partner.commercial_partner_id.id]),
                ('agent_id', '=', partner.id),
                ('state', '=', 'sent'),
            ]
        return domain
