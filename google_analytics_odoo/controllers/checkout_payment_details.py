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
import logging
import requests
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request

_logger = logging.getLogger(__name__)


class CheckoutAndPayments(WebsiteSale):
    """Extends the functionality of the website sale process by adding
       analytics events when a user checks out and makes a payment."""

    @http.route(['/shop/confirmation'], type='http', auth="public",
                website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        """Sends an event when a customer completes payment in the website shop."""
        res = super().shop_payment_confirmation(**post)
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            try:
                enable_analytics = request.env[
                    'ir.config_parameter'].sudo().get_str(
                    'google_analytics_odoo.enable_analytics'
                )
                measurement_id = request.env[
                    'ir.config_parameter'].sudo().get_str(
                    'google_analytics_odoo.measurement_id_analytics'
                )
                api_secret = request.env['ir.config_parameter'].sudo().get_str(
                    'google_analytics_odoo.api_secret'
                )
                if enable_analytics and measurement_id and api_secret:
                    products = ",".join(line.name for line in order.order_line if line.name)
                    url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"
                    data = {
                        "client_id": str(request.env.user.id),
                        "events": [{
                            "name": "Online_payments",
                            "params": {
                                "Product_Name": products,
                                "Customer": request.env.user.name,
                                "Total_Quantity": order.cart_quantity,
                                "Total_Price": order.amount_total,
                                "Total_Tax": order.amount_tax,
                            }
                        }]
                    }
                    requests.post(url, json=data, timeout=5)
            except Exception as e:
                _logger.warning("Google Analytics Online_payments error: %s", e)
        return res

    @http.route('/shop/payment', type='http', auth='public', website=True,
                sitemap=False)
    def shop_payment(self, **post):
        """Sends an event to Google Analytics when a user checks out the products in the cart."""
        res = super().shop_payment(**post)
        order_id = request.session.get('sale_order_id')
        if order_id:
            order = request.env['sale.order'].sudo().browse(order_id)
            try:
                enable_analytics = request.env[
                    'ir.config_parameter'].sudo().get_str(
                    'google_analytics_odoo.enable_analytics'
                )
                measurement_id = request.env[
                    'ir.config_parameter'].sudo().get_str(
                    'google_analytics_odoo.measurement_id_analytics'
                )
                api_secret = request.env['ir.config_parameter'].sudo().get_str(
                    'google_analytics_odoo.api_secret'
                )
                if enable_analytics and measurement_id and api_secret:
                    products = ",".join(line.name for line in order.order_line if line.name)
                    url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"
                    data = {
                        "client_id": str(request.env.user.id),
                        "events": [{
                            "name": "Cart_Checkout",
                            "params": {
                                "Product_Name": products,
                                "Customer": request.env.user.name,
                                "Total_Quantity": order.cart_quantity,
                                "Total_Price": order.amount_total,
                                "Total_Tax": order.amount_tax,
                            }
                        }]
                    }
                    requests.post(url, json=data, timeout=5)
            except Exception as e:
                _logger.warning("Google Analytics Cart_Checkout error: %s", e)
        return res
