# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
import base64
import json
import requests
from odoo import _
from odoo.exceptions import UserError
import logging
from odoo import http
from odoo.http import request
_logger = logging.getLogger(__name__)


class SaferPay(http.Controller):
    """For connecting safer pay payment acquirer with odoo """

    @http.route('/saferpay/payment', type='json', auth='public', website=True)
    def saferpay_payment(self, reference):
        """ Connect with safer pay payment gateway"""
        base_url = request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        transaction = request.env['payment.transaction'].sudo().search(
            [('reference', '=', reference)])
        amount = int((transaction.amount * 0.011) * 100)
        sequence = transaction.reference
        order = request.env['sale.order'].sudo().search(
            [('name', '=', sequence)])
        provider_details = request.env.ref('safer_pay.payment_acquirer_data')
        if provider_details.customer and provider_details.terminal:
            credentials = f"{provider_details.username}:{provider_details.password}"
            base64_credentials = base64.b64encode(
                credentials.encode('utf-8')).decode('utf-8')
            authorization_header = f'Basic {base64_credentials}'
            url = "https://test.saferpay.com/api/Payment/v1/PaymentPage/Initialize"
            payload = json.dumps({
                "RequestHeader": {
                    "SpecVersion": "1.33",
                    "CustomerId": str(provider_details.customer),
                    "RequestId": "1",
                    "RetryIndicator": 0
                },
                "TerminalId": str(provider_details.terminal),
                "Payment": {
                    "Amount": {
                        "Value": str(amount),
                        "CurrencyCode": "CHF"
                    },
                    "OrderId": str(order.id),
                    "Description": str(sequence)
                },
                "ReturnUrl": {
                    "Url": base_url + "/shop/confirmation",
                }
            })
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json',
                'SpecVersion': '1.33',
                'RetryIndicator': '0',
                'Authorization':
                    authorization_header,
                'Cookie': 'ASP.NET_SessionId=lr0an2dywf25itkugaam32pm; PREF=C=en'
            }
            response = requests.request("POST", url, headers=headers,
                                        data=payload)
            text = response.json()
            website = request.env['website'].get_current_website()
            sale_order = website.sale_get_order(force_create=True)
            if sale_order.state != 'draft':
                request.session['sale_order_id'] = None
                sale_order = website.sale_get_order(
                    force_create=True)
            sale_order.write({
                'state': 'sale',
                'payment': False
            })
            if text.get('RedirectUrl'):
                sale_order.write({
                    'payment': False,
                    'sale_order': sale_order.id,
                })
                redirect_url = text['RedirectUrl']
                return redirect_url
            else:
                sale_order.write({
                    'payment': True
                })
                return False
        else:
            raise UserError(_("Please set the credential."))
