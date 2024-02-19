# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import requests
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class CheckoutAndPayments(WebsiteSale):
    """ Extends the functionality of the website sale process by adding
        sending events to Google Analytics whe aa use checkout and do a
        payment."""
    @http.route(['/shop/confirmation'], type='http', auth="public",
                website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        """ overriding the function to send an event when a customer do payment
        in the website shop """
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            values = self._prepare_shop_payment_confirmation_values(order)
            enable_analytics = request.env[
                'ir.config_parameter'].sudo().get_param(
                'google_analytics_odoo.enable_analytics'),
            measurement_id = request.env[
                'ir.config_parameter'].sudo().get_param(
                'google_analytics_odoo.measurement_id_analytics')
            api_secret = request.env['ir.config_parameter'].sudo().get_param(
                'google_analytics_odoo.api_secret')
            products = ""
            for line in order.order_line:
                products += line.name + ','
            if enable_analytics:
                url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"
                data = {
                    "client_id": str(request.env.user.id),
                    "events": [{
                        "name": "Online_payments",
                        "params": {
                            "Product_Name": products,
                            'Customer': request.env.user.name,
                            "Total_Quantity": order.cart_quantity,
                            "Total_Price": order.amount_total,
                            "Total_Tax": order.amount_tax,
                        }
                    }]
                }
                requests.post(url, json=data)
            return request.render("website_sale.confirmation", values)
        else:
            return request.redirect('/shop')

    @http.route('/shop/payment', type='http', auth='public', website=True,
                sitemap=False)
    def shop_payment(self, **post):
        """Supering the function to send an event to Google Analytics when
        a user checkout the products in the cart"""
        res = super().shop_payment(**post)
        order = request.website.sale_get_order()
        enable_analytics = request.env[
            'ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.enable_analytics'),
        measurement_id = request.env[
            'ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.measurement_id_analytics')
        api_secret = request.env['ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.api_secret')
        products = ""
        for line in order.order_line:
            products += line.name + ','
        if enable_analytics:
            url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"
            data = {
                "client_id": str(request.env.user.id),
                "events": [{
                    "name": "Cart_Checkout",
                    "params": {
                        "Product_Name": products,
                        'Customer': request.env.user.name,
                        "Total_Quantity": order.cart_quantity,
                        "Total_Price": order.amount_total,
                        "Total_Tax": order.amount_tax,
                    }
                }]
            }
            requests.post(url, json=data)
        return res
