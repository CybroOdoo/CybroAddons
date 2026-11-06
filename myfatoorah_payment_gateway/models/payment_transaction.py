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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
# pylint: disable=missing-module-docstring,too-few-public-methods,too-many-locals
# pylint: disable=protected-access,attribute-defined-outside-init
import json
import logging

import requests

from odoo import api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Inherited class of payment transaction to add MyFatoorah functions."""
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Function to fetch the values of the payment gateway"""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'myfatoorah':
            return res
        return self.send_payment()

    def send_payment(self):
        """Send payment information to MyFatoorah for processing."""
        provider = self.provider_id
        base_api_url = provider._myfatoorah_get_api_url()
        api_url = f"{base_api_url}v2/SendPayment"
        api_key = provider.myfatoorah_token
        odoo_base_url = self.get_base_url()
        mobile_country_code = self.partner_id.country_id.phone_code
        phone_number = self.partner_phone
        if not phone_number:
            msg = "Please provide the phone number."
            raise ValueError(msg)
        phone_number = phone_number.replace(str(mobile_country_code), '')
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
        if not phone_number:
            msg = "Please provide the phone number in proper format"
            raise ValueError(msg)
        currency = self.currency_id.name
        sendpay_data = {
            "NotificationOption": "ALL",
            "CustomerName": self.partner_name,
            "DisplayCurrencyIso": currency,
            "MobileCountryCode": mobile_country_code,
            "CustomerMobile": phone_number,
            "CustomerEmail": self.partner_email,
            "InvoiceValue": self.amount,
            "CallBackUrl": f"{odoo_base_url}/payment/myfatoorah/_return_url",
            "ErrorUrl": f"{odoo_base_url}/payment/myfatoorah/failed",
            "Language": "en",
            "CustomerReference": self.reference,
            "CustomerAddress": {
                "Address": (
                    f'{self.partner_address} ,{self.partner_city} '
                    f'{self.partner_zip} ,{self.partner_state_id.name} ,'
                    f'{self.partner_country_id.name}'
                ),
            },
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
        payload = json.dumps(sendpay_data)
        response = requests.request("POST", api_url, headers=headers, data=payload, timeout=60)
        response_data = response.json()
        if not response_data.get('IsSuccess'):
            validation_errors = response_data.get('ValidationErrors')
            if validation_errors:
                error_message = validation_errors[0].get('Error')
                raise ValidationError(self.env._("MyFatoorah: %s", error_message))
        if response_data.get('Data', {}).get('InvoiceURL'):
            payment_url = response_data.get('Data')['InvoiceURL']
            sendpay_data['InvoiceURL'] = payment_url
        return {
            'api_url': f"{odoo_base_url}/payment/myfatoorah/response",
            'data': sendpay_data,
        }

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        """Extract the CustomerReference (our internal tx reference) from the
        MyFatoorah GetPaymentStatus payload."""
        if provider_code != 'myfatoorah':
            return super()._extract_reference(provider_code, payment_data)
        return payment_data.get('CustomerReference') or payment_data.get('reference')

    def _validate_amount(self, payment_data):
        """Validate the transaction against the payment data received.

        We deliberately do NOT compare InvoiceValue against self.amount
        for MyFatoorah. In testing, GetPaymentStatus was observed to
        return InvoiceValue in the settlement currency of the local
        payment method actually used (e.g. KWD when paying via KNET/Benefit)
        rather than the original DisplayCurrencyIso (e.g. USD).
        """
        self.ensure_one()
        if self.provider_code != 'myfatoorah':
            return super()._validate_amount(payment_data)

        if self.operation == 'validation':
            return None

        invoice_value = payment_data.get('InvoiceValue')
        transactions = payment_data.get('InvoiceTransactions') or []
        last_tx = transactions[-1] if transactions else {}
        _logger.info(
            "MyFatoorah payment data for tx %s: tx.amount=%s %s, "
            "reported InvoiceValue=%s, PaidCurrency=%s, PaidCurrencyValue=%s, "
            "InvoiceStatus=%s",
            self.reference, self.amount, self.currency_id.name, invoice_value,
            last_tx.get('PaidCurrency'), last_tx.get('PaidCurrencyValue'),
            payment_data.get('InvoiceStatus'),
        )
        return None

    def _apply_updates(self, payment_data):
        """Update the transaction's state based on MyFatoorah's InvoiceStatus."""
        self.ensure_one()
        if self.provider_code != 'myfatoorah':
            return super()._apply_updates(payment_data)

        transactions = payment_data.get('InvoiceTransactions') or []
        if transactions:
            provider_ref = (
                transactions[-1].get('PaymentId')
                or transactions[-1].get('TransactionId')
            )
            if provider_ref:
                self.provider_reference = str(provider_ref)
        elif payment_data.get('InvoiceId'):
            self.provider_reference = str(payment_data.get('InvoiceId'))

        invoice_status = payment_data.get('InvoiceStatus')
        if invoice_status == 'Paid':
            self._set_done()
        elif invoice_status == 'Pending':
            self._set_pending()
        elif invoice_status in ('Failed', 'Expired', 'Canceled'):
            self._set_error(
                self.env._("MyFatoorah: the payment has status \"%s\".", invoice_status),
            )
        else:
            self._set_error(
                self.env._(
                    "MyFatoorah: received data with invalid or missing invoice status (%s).",
                    invoice_status,
                ),
            )
        return None
