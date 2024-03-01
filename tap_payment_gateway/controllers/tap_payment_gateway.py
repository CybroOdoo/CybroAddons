# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Jabin MP (odoo@cybrosys.com)
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
import logging
import re
import requests
from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class TapPaymentGateway(http.Controller):
    """Controller for handling payment processing using the Tap Payment
    Gateway."""

    @http.route('/tap', type='json', auth='public', methods=['POST'],
                csrf=False)
    def generate_tap_token(self, card_number, exp_month, exp_year, cvc,
                           cardholder_name):
        """Generate a Tap Payment Gateway token for a given credit card."""
        special_chars_regex = re.compile(
            r'[@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]+')
        if special_chars_regex.search(cardholder_name):
            raise ValidationError(_('Invalid Card Holder Name'))
        tap_credentials = http.request.env.ref(
            'tap_payment_gateway.payment_provider_tap').sudo()
        token_url = "https://api.tap.company/v2/tokens"
        payload = {
            "card": {
                "number": card_number,
                "exp_month": exp_month,
                "exp_year": exp_year,
                "cvc": cvc,
                "name": cardholder_name,
            },
            "client_ip": http.request.httprequest.remote_addr
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {tap_credentials.tap_secret_key}"
        }
        try:
            response = requests.post(token_url, json=payload, headers=headers)
            if response.status_code == 200:
                token_data = response.json()
                return token_data['id']
            else:
                error_message = response.json().get('message',
                                                    'Token creation failed')
                _logger.error(f"Token creation failed: {error_message}")
                return None
        except Exception as e:
            _logger.error(f"An error occurred: {str(e)}")
            return None

    @http.route('/payment/tap/process_payment', type='json', auth='public')
    def tap_process_payment(self, payload, data):
        """Process a payment using the Tap Payment Gateway."""
        tap_credentials = http.request.env.ref(
            'tap_payment_gateway.payment_provider_tap').sudo()
        card_token = payload
        payment_url = "https://api.tap.company/v2/charges"
        partner = request.env['res.partner'].sudo().browse(data['partner_id'])
        redirect_url = request.httprequest.host_url + 'payment/status'
        payload = {
            "amount": str(data['amount']),
            "currency": data.get('currency', 'KWD'),
            "description": data['reference'],
            "source": {
                "id": card_token,
                "type": "card"
            },
            "customer": {
                "first_name": partner.sudo().name,
                "last_name": "",
                "email": partner.sudo().email,
                "phone": {
                    "number": partner.sudo().phone
                }
            },
            "redirect": {"url": redirect_url}}
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {tap_credentials.tap_secret_key}"
        }
        try:
            response = requests.post(payment_url, json=payload,
                                     headers=headers)
            if response.status_code == 200:
                payment_data = response.json()
                tap_sudo = (request.env['payment.transaction'].sudo()
                            ._get_tx_from_notification_data('tap',
                                                            payment_data))
                tap_sudo._process_notification_data(payment_data)
                payment_url = payment_data['redirect']['url']
                return {'success': True, 'payment_url': payment_url}
            else:
                error_message = response.json().get('message',
                                                    'Payment processing failed')
                _logger.error(f"Payment processing failed: {error_message}")
                return False
        except Exception as e:
            _logger.error(
                f"An error occurred during payment processing: {str(e)}")
            return False
