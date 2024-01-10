# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Subina P(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.
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
##############################################################################
import json
import logging
import requests
from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Model is inherited to define functon to execute different payment
    operations for MyFatoorah payment acquirer."""
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """Get payment rendering values and execute payment operation"""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'myfatoorah':
            return res
        return self.execute_payment()

    def execute_payment(self):
        """Fetching data and Executing Payment"""
        base_api_url = self.env['payment.acquirer'].search(
            [('provider', '=', 'myfatoorah')])._myfatoorah_get_api_url()
        api_url = f"{base_api_url}v2/ExecutePayment"
        api_key = (self.env['payment.acquirer'].
                   search([('provider', '=', 'myfatoorah')]).myfatoorah_token)
        odoo_base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url')
        payment_transaction = self
        sale_order = payment_transaction.sale_order_ids
        order_line = sale_order.order_line
        invoice_items = [
            {
                'ItemName': rec.product_id.name,
                'Quantity': int(rec.product_uom_qty),
                'UnitPrice': rec.price_unit,
            }
            for rec in order_line
        ]
        if len(self.partner_phone.replace('-', "").rsplit(' ', 1)[1]) > 11:
            raise ValidationError(_("Phone number must not  be greater than "
                                    "11 characters"))
        payment_details = {
            "PaymentMethodId": 6,
            "CustomerName": self.partner_name,
            "DisplayCurrencyIso": self.currency_id.name,
            "CustomerMobile":
                self.partner_phone.replace('-', "").rsplit(' ', 1)[1],
            "CustomerEmail": self.partner_email,
            "InvoiceValue": (self.amount - sale_order.amount_tax),
            "CallBackUrl": f"{odoo_base_url}/payment/myfatoorah/_return_url",
            "ErrorUrl": f"{odoo_base_url}/payment/myfatoorah/_return_url",
            "Language": "en",
            "CustomerReference": self.reference,
            "CustomerAddress": {
            "Address": f'{self.partner_address}, {self.partner_city}, '
                       f'{self.partner_zip}, {self.partner_state_id.name}, '
                       f'{self.partner_country_id.name}',
            },
            "InvoiceItems":
                invoice_items
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
        payload = json.dumps(payment_details)
        response = requests.request("POST", api_url, headers=headers,
                                    data=payload)
        response_data = response.json()
        payment_url = response_data.get('Data')['PaymentURL']
        payment_details['PaymentURL'] = payment_url
        return {
            'api_url': f"{odoo_base_url}/payment/myfatoorah/response",
            'data': payment_details,
        }

    def _get_tx_from_feedback_data(self, provider, notification_data):
        """Getting  payment status from myfatoorah"""
        api_key = self.env['payment.acquirer'].search(
            [('provider', '=', 'myfatoorah')]).myfatoorah_token
        base_api_url = self.env['payment.acquirer'].search(
            [('provider', '=', 'myfatoorah')])._myfatoorah_get_api_url()
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
        response = requests.request("POST", url, headers=headers,
                                    data=payload)
        response_data = response.json()
        received_tx = super()._get_tx_from_feedback_data('myfatoorah',
                                                    notification_data)
        if provider != 'myfatoorah' or len(received_tx) == 1:
            return received_tx
        reference = response_data["Data"]["CustomerReference"]
        received_tx = self.search(
            [
                ('reference', '=', reference),
                ('provider', '=', 'myfatoorah')])
        if not received_tx:
            raise ValidationError(
                "myfatoorah: " + _(
                    "No transaction found matching reference %s.",
                    reference)
            )
        return received_tx

    def _handle_feedback_data(self, provider, notification_data):
        """Handle notification data and execute callback"""
        received_tx = self._get_tx_from_feedback_data(provider,
                                                 notification_data)
        received_tx._process_feedback_data(notification_data)
        received_tx._execute_callback()
        return received_tx

    def _process_feedback_data(self, notification_data):
        """Process the notification data."""
        super()._process_feedback_data(notification_data)
        if self.provider == 'myfatoorah':
            self._set_done()
