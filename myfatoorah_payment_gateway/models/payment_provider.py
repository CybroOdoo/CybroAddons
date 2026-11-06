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
# pylint: disable=missing-module-docstring,too-few-public-methods
import json
import logging

import requests

from odoo import fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    """ Inherited class of payment provider to add myfatoorah functions"""
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('myfatoorah', "MyFatoorah")],
        ondelete={'myfatoorah': 'set default'},
        help="Select 'MyFatoorah' as payment provider to process payments through MyFatoorah.",
    )
    myfatoorah_token = fields.Char(
        string='Token',
        required_if_provider='myfatoorah',
        copy=False,
        help="Authentication token required for integrating with MyFatoorah's payment gateway.",
    )

    def _get_default_payment_method_codes(self):
        """ Return the default payment method codes for MyFatoorah. """
        self.ensure_one()
        if self.code != 'myfatoorah':
            return super()._get_default_payment_method_codes()
        return {'myfatoorah'}

    def _myfatoorah_get_api_url(self):
        """Return the API URL according to the provider state."""
        self.ensure_one()
        return 'https://api.myfatoorah.com/' if self.is_live else 'https://apitest.myfatoorah.com/'

    def _myfatoorah_get_payment_status(self, payment_id):
        """Call MyFatoorah's GetPaymentStatus endpoint and return the 'Data' payload.

        This centralizes the status lookup so it can be called once by the controller
        after the customer is redirected back from MyFatoorah, and the resulting data
        is then recorded via payment.transaction._record().

        :param str payment_id: The MyFatoorah PaymentId received on the return URL.
        :return: The 'Data' dict of the GetPaymentStatus response.
        :rtype: dict
        """
        self.ensure_one()
        if not self.myfatoorah_token:
            raise ValidationError(
                self.env._("MyFatoorah: Payment provider is missing an API token."),
            )
        base_api_url = self._myfatoorah_get_api_url()
        url = f"{base_api_url}v2/GetPaymentStatus"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.myfatoorah_token}',
        }
        payload = json.dumps({"Key": str(payment_id), "KeyType": "PaymentId"})
        response = requests.request("POST", url, headers=headers, data=payload, timeout=60)
        try:
            response_data = response.json()
        except (ValueError, requests.exceptions.RequestException) as exc:
            _logger.error(
                "MyFatoorah GetPaymentStatus HTTP error %s for payment id %s: %s",
                response.status_code, payment_id, response.text,
            )
            raise ValidationError(
                self.env._(
                    "MyFatoorah: received invalid response from server (HTTP %s).",
                    response.status_code,
                ),
            ) from exc
        if not response_data.get('IsSuccess'):
            _logger.warning(
                "MyFatoorah GetPaymentStatus failed for payment id %s:\n%s",
                payment_id, response_data,
            )
            raise ValidationError(
                self.env._(
                    "MyFatoorah: could not retrieve the payment status for payment %s.",
                    payment_id,
                ),
            )
        return response_data.get('Data') or {}
