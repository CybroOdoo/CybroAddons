# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina (odoo@cybrosys.com)
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
# Import required libraries (make sure it is installed!)
import logging
from odoo import _, models
from odoo.exceptions import ValidationError
import requests
import json

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
        base_api_url = self.env['payment.provider'].search([('code', '=', 'myfatoorah')])._myfatoorah_get_api_url()
        api_url = f"{base_api_url}v2/SendPayment"
        api_key = self.env['payment.provider'].search([('code', '=', 'myfatoorah')]).myfatoorah_token
        odoo_base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url')
        sale_order = self.env['payment.transaction'].search(
            [('id', '=', self.id)]).sale_order_ids
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
        currency = self.env.company.currency_id.name
        sendpay_data = {
            "NotificationOption": "ALL",
            "CustomerName": self.partner_name,
            "DisplayCurrencyIso": currency,
            "MobileCountryCode": MobileCountryCode,
            "CustomerMobile": phone_number,
            "CustomerEmail": self.partner_email,
            "InvoiceValue": (self.amount - sale_order.amount_tax),
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

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Getting  payment status from myfatoorah"""
        api_key = self.env['payment.provider'].search(
            [('code', '=', 'myfatoorah')]).myfatoorah_token
        base_api_url = self.env['payment.provider'].search(
            [('code', '=', 'myfatoorah')])._myfatoorah_get_api_url()
        url = f"{base_api_url}v2/GetPaymentStatus"
        paymentid = notification_data.get('paymentId')
        payload = json.dumps({
            "Key": f"{paymentid}",
            "KeyType": "paymentId"
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
        response = requests.request("POST", url,
                                    headers=headers, data=payload)
        response_data = response.json()
        tx = super()._get_tx_from_notification_data(provider_code,
                                                    notification_data)
        if provider_code != 'myfatoorah' or len(tx) == 1:
            return tx
        domain = [('provider_code', '=', 'myfatoorah')]
        reference = ""
        if response_data["Data"]["CustomerReference"]:
            reference = response_data["Data"]["CustomerReference"]
            domain.append(('reference', '=', str(reference)))
        if tx := self.search(domain):
            return tx
        else:
            raise ValidationError(
                "myfatoorah: " + _(
                    "No transaction found matching reference %s.",
                    reference)
            )

    def _handle_notification_data(self, provider_code, notification_data):
        """Function to handle the notification data """
        tx = self._get_tx_from_notification_data(provider_code,
                                                 notification_data)
        tx._process_notification_data(notification_data)
        tx._execute_callback()
        return tx

    def _process_notification_data(self, notification_data):
        """ Function to process the notification data"""
        super()._process_notification_data(notification_data)
        if self.provider_code != 'myfatoorah':
            return
        else:
            self._set_done()
