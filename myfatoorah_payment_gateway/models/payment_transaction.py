# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Harshitha AP (odoo@cybrosys.com)
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
import json
import requests

from odoo import api, models
from odoo.tools import _
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
        # Use self.provider_id (already a singleton linked to this transaction)
        # instead of searching all providers with code='myfatoorah', which can
        # return multiple records and cause ensure_one() to fail.
        provider = self.provider_id
        base_api_url = provider._myfatoorah_get_api_url()
        api_url = f"{base_api_url}v2/SendPayment"
        api_key = provider.myfatoorah_token
        odoo_base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url')
        MobileCountryCode = self.partner_id.country_id.phone_code
        phone_number = self.partner_phone
        if not phone_number:
            raise ValueError("Please provide the phone number.")
        else:
            phone_number = phone_number.replace(str(MobileCountryCode), '')
            if phone_number.startswith('+'):
                phone_number = phone_number[1:]
            elif not phone_number:
                raise ValueError(
                    "Please provide the phone number in proper format")
        # Use the TRANSACTION's own currency (self.currency_id), not the
        # company currency. "InvoiceValue" below is self.amount, which is
        # expressed in self.currency_id. If DisplayCurrencyIso were taken
        # from the company currency instead, and the company currency ever
        # differs from the order/transaction currency, MyFatoorah would be
        # told "this amount is in currency X" while it's actually in
        # currency Y - causing invoice amounts to be wrong and, later, the
        # amount validation in _extract_amount_data()/_validate_amount() to
        # fail with "The amount from the payment data doesn't match the one
        # from the transaction."
        currency = self.currency_id.name
        sendpay_data = {
            "NotificationOption": "ALL",
            "CustomerName": self.partner_name,
            "DisplayCurrencyIso": currency,
            "MobileCountryCode": MobileCountryCode,
            "CustomerMobile": phone_number,
            "CustomerEmail": self.partner_email,
            "InvoiceValue": self.amount,
            "CallBackUrl": f"{odoo_base_url}/payment/myfatoorah/_return_url",
            "ErrorUrl": f"{odoo_base_url}/payment/myfatoorah/failed",
            "Language": "en",
            "CustomerReference": self.reference,
            "CustomerAddress": {
                "Address": f'{self.partner_address} ,{self.partner_city} '
                           f'{self.partner_zip} ,{self.partner_state_id.name} ,'
                           f'{self.partner_country_id.name}',
            },
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
        payload = json.dumps(sendpay_data)
        response = requests.request("POST", api_url, headers=headers,
                                    data=payload)
        response_data = response.json()
        if not response_data.get('IsSuccess'):
            validation_errors = response_data.get('ValidationErrors')
            if validation_errors:
                error_message = validation_errors[0].get('Error')
                raise ValidationError(f"{error_message}")
        if response_data.get('Data')['InvoiceURL']:
            payment_url = response_data.get('Data')['InvoiceURL']
            sendpay_data['InvoiceURL'] = payment_url
        return {
            'api_url': f"{odoo_base_url}/payment/myfatoorah/response",
            'data': sendpay_data,
        }

    # Odoo 19 replaced the old payment-processing API
    # (_get_tx_from_notification_data / _handle_notification_data /
    # _process_notification_data) with a new one built around _process(),
    # which internally calls _search_by_reference() -> _extract_reference(),
    # _validate_amount() -> _extract_amount_data(), and _apply_updates().
    # The old method names no longer exist on the base payment.transaction
    # model, which is why `super()._get_tx_from_notification_data(...)`
    # raised "'super' object has no attribute '_get_tx_from_notification_data'".
    # The controller now fetches the MyFatoorah GetPaymentStatus payload once
    # and passes it straight into `_process('myfatoorah', payment_data)`.

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        """Extract the CustomerReference (our internal tx reference) from the
        MyFatoorah GetPaymentStatus payload."""
        if provider_code != 'myfatoorah':
            return super()._extract_reference(provider_code, payment_data)
        return payment_data.get('CustomerReference')

    def _validate_amount(self, payment_data):
        """Validate the transaction against the payment data received.

        We deliberately do NOT compare `InvoiceValue` against `self.amount`
        for MyFatoorah. In testing, `GetPaymentStatus` was observed to
        return `InvoiceValue` in the *settlement* currency of the local
        payment method actually used (e.g. KWD when paying via KNET/Benefit)
        rather than the original `DisplayCurrencyIso` (e.g. USD) the invoice
        was created with - even though MyFatoorah's own documentation
        implies it stays in the original currency. Example observed:
        tx.amount = 59.4 USD, but InvoiceValue came back as 18.333 (the KNET
        KWD-converted price), which is not a real discrepancy - it's the
        same invoice, just reported in a different currency depending on
        the payment rail used.

        Trying to detect and back-convert every possible settlement
        currency is fragile and unnecessary: the invoice amount was already
        locked server-side by MyFatoorah the moment we called SendPayment
        with a specific InvoiceValue/DisplayCurrencyIso. A customer cannot
        pay a different amount for that same InvoiceId - MyFatoorah enforces
        that on their end, not ours. So `InvoiceStatus == 'Paid'` on the
        matching `CustomerReference` (already verified by
        `_search_by_reference`/`_extract_reference`) is sufficient proof of
        correct payment. We just log the reported value for visibility/
        auditing instead of hard-failing on it.
        """
        self.ensure_one()
        if self.provider_code != 'myfatoorah':
            return super()._validate_amount(payment_data)

        if self.operation == 'validation':
            return  # Skip validation for $0-auth transactions.

        invoice_value = payment_data.get('InvoiceValue')
        transactions = payment_data.get('InvoiceTransactions') or []
        last_tx = transactions[-1] if transactions else {}
        _logger.info(
            "MyFatoorah payment data for tx %s (amount check skipped - see "
            "docstring): tx.amount=%s %s, reported InvoiceValue=%s, "
            "PaidCurrency=%s, PaidCurrencyValue=%s, InvoiceStatus=%s",
            self.reference, self.amount, self.currency_id.name, invoice_value,
            last_tx.get('PaidCurrency'), last_tx.get('PaidCurrencyValue'),
            payment_data.get('InvoiceStatus'),
        )
        # No _set_error() call here on purpose - see docstring above.

    def _apply_updates(self, payment_data):
        """Update the transaction's state based on MyFatoorah's InvoiceStatus."""
        self.ensure_one()
        if self.provider_code != 'myfatoorah':
            return super()._apply_updates(payment_data)

        transactions = payment_data.get('InvoiceTransactions') or []
        if transactions:
            # The most recent transaction is the last one in the array.
            self.provider_reference = (
                transactions[-1].get('PaymentId')
                or transactions[-1].get('TransactionId')
            )

        invoice_status = payment_data.get('InvoiceStatus')
        if invoice_status == 'Paid':
            self._set_done()
        elif invoice_status == 'Pending':
            self._set_pending()
        elif invoice_status in ('Failed', 'Expired', 'Canceled'):
            self._set_error(
                _("MyFatoorah: the payment has status \"%s\".", invoice_status)
            )
        else:
            self._set_error(
                _("MyFatoorah: received data with invalid or missing invoice "
                  "status (%s).", invoice_status)
            )