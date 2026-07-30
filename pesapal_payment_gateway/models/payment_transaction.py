# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
import json
import logging
import uuid

import requests

from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Inherits the model payment transaction to add the functionalities for
    the pesapal payment gateway"""
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """Fetch the values of the payment gateway for the redirect form.

        NOTE: Do NOT call _set_pending() here — this method runs during form
        rendering, before the user even sees the Pesapal page. Setting pending
        here causes Odoo to consider the sale order confirmed (empties cart)
        prematurely. The state transition happens in _process_notification_data
        when we receive the callback from Pesapal.
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'pesapal':
            return res
        access_token = self.authenticate_payment()
        if not access_token:
            _logger.error("Pesapal: failed to obtain access token for tx %s",
                          self.reference)
            return res
        result = self._pesapal_register_ipn_url(token=access_token)
        return result or res

    def authenticate_payment(self):
        """Method authenticate_payment to fetch the access token"""
        url = self.provider_id.token_request_url
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json'}
        payload = {'consumer_key': self.provider_id.pesapal_consumer_key,
                   'consumer_secret': self.provider_id.pesapal_consumer_secret}
        try:
            response = requests.post(url, headers=headers,
                                     data=json.dumps(payload), timeout=20)
            response.raise_for_status()
            token = response.json()['token']
            return token
        except requests.exceptions.RequestException as exception:
            _logger.error(
                "Pesapal: error creating access token: %s", exception)
            return None

    def _pesapal_register_ipn_url(self, token):
        """Method to register IPN URL in Pesapal"""
        url = self.provider_id.token_register_url
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + token}
        odoo_base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url')
        ipn_url = f"{odoo_base_url}/payment/pesapal/_return_url"
        payload = {'url': ipn_url,
                   'ipn_notification_type': 'GET'}
        try:
            response = requests.post(url, headers=headers,
                                     data=json.dumps(payload),
                                     timeout=20)
            response.raise_for_status()
            response_data = response.json()
            ipn_id = response_data.get('ipn_id')
            return self._pesapal_submit_order_request(
                token=token,
                odoo_base_url=odoo_base_url,
                ipn_id=ipn_id)
        except requests.exceptions.RequestException as exception:
            _logger.error("Pesapal: error registering IPN URL: %s", exception)
            return None

    def _pesapal_submit_order_request(self, token, odoo_base_url, ipn_id):
        """Method to submit the payment order request"""
        url = self.provider_id.payment_submit_url
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + token}
        currency = self.currency_id.name
        mobile_country_code = self.partner_id.country_id.phone_code
        billing_country_code = self.partner_id.country_id.code or ""
        phone_number = self.partner_phone
        if not phone_number:
            raise ValueError("Please provide the phone number.")
        phone_number = phone_number.strip()
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        # Remove country code digits from the front if present
        country_code_str = str(mobile_country_code)
        if phone_number.startswith(country_code_str):
            phone_number = phone_number[len(country_code_str):]
        order_id = str(uuid.uuid4())
        order_data = {
            "id": order_id,
            "currency": currency,
            "amount": self.amount,
            "description": self.reference,
            "callback_url": f"{odoo_base_url}/payment/pesapal/_return_url",
            "notification_id": ipn_id,
            "billing_address": {
                "email_address": self.partner_email,
                "phone_number": phone_number,
                "country_code": billing_country_code,
                "first_name": self.partner_name,
                "middle_name": "",
                "last_name": "",
                "line_1": self.partner_address,
                "line_2": "",
                "city": self.partner_city,
                "state": self.partner_state_id.name if self.partner_state_id else "",
                "postal_code": self.partner_zip or "",
                "zip_code": self.partner_zip or ""
            }
        }
        try:
            response = requests.post(url, headers=headers,
                                     data=json.dumps(order_data), timeout=10)
            response.raise_for_status()
            response_data = response.json()
            _logger.info("Pesapal SubmitOrderRequest response for tx %s: %s",
                         self.reference, response_data)
            order_tracking_id = response_data.get("order_tracking_id")
            redirect_url = response_data.get("redirect_url")
            # Store the UUID we sent as provider_reference so the callback
            # can look up this transaction via OrderMerchantReference.
            self.provider_reference = order_id
            order_data['order_tracking_id'] = order_tracking_id
            order_data['redirect_url'] = redirect_url
            return {
                'api_url': f"{odoo_base_url}/payment/pesapal/response",
                'data': order_data,
                'token': token
            }
        except requests.exceptions.RequestException as exception:
            _logger.error("Pesapal: error submitting order: %s", exception)
            return None

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Find the transaction from Pesapal notification data.

        Pesapal sends back 'OrderMerchantReference' which is the UUID we
        originally sent as the order id. We stored that UUID in
        provider_reference, so we look up by provider_reference.
        """
        tx = super()._get_tx_from_notification_data(provider_code,
                                                     notification_data)
        if provider_code != 'pesapal':
            return tx
        order_merchant_ref = notification_data.get('OrderMerchantReference')
        if not order_merchant_ref:
            raise ValidationError(
                "Pesapal: " + _(
                    "Received notification data with missing merchant reference."))
        tx = self.search(
            [('provider_reference', '=', order_merchant_ref),
             ('provider_code', '=', 'pesapal')], limit=1)
        if not tx:
            tx = self.search(
                [('reference', '=', order_merchant_ref),
                 ('provider_code', '=', 'pesapal')], limit=1)
        if not tx:
            raise ValidationError(
                "Pesapal: " + _(
                    "No transaction found matching reference %s.",
                    order_merchant_ref)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """Process the Pesapal notification data and update the transaction
        state based on the payment status from Pesapal's status API.

        This is the correct place to call _set_pending(), _set_done(), etc.
        — not during rendering.
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'pesapal':
            return

        order_tracking_id = notification_data.get('OrderTrackingId')
        access_token = self.authenticate_payment()

        if not access_token:
            _logger.error("Pesapal: failed to obtain access token for tx %s",
                          self.reference)
            self._set_error(
                "Pesapal: authentication failure during status check.")
            return

        if not order_tracking_id:
            _logger.error("Pesapal: missing OrderTrackingId for tx %s",
                          self.reference)
            self._set_error(
                "Pesapal: missing OrderTrackingId in callback.")
            return

        status_url = self.provider_id.payment_status_url
        url = f"{status_url}{order_tracking_id}"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.RequestException as e:
            _logger.error("Pesapal: status check failed for tx %s: %s",
                          self.reference, e)
            self._set_error(f"Pesapal: status check failed — {e}")
            return

        _logger.info("Pesapal status API response for tx %s: %s",
                     self.reference, response_data)

        payment_status = (
            response_data.get("payment_status_description", "")
            .strip()
            .lower()
        )

        error = response_data.get("error") or {}
        error_code = error.get("code", "")

        if payment_status == "completed":
            self._set_done()

        elif payment_status in ("failed", "reversed"):
            self._set_canceled()

        elif payment_status == "invalid":
            if error_code == "payment_details_not_found":
                _logger.info(
                    "Payment details not yet available from Pesapal. Keeping transaction pending."
                )
                self._set_pending()
                return
            else:
                self._set_canceled()

        else:
            self._set_pending()