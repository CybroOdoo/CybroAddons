# -*- coding: utf-8 -*-
###############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import logging
import requests
from requests.exceptions import RequestException

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.payment.logging import get_payment_logger

_logger = get_payment_logger(__name__)

BITPAY_TEST_URL = 'https://test.bitpay.com'
BITPAY_PRODUCTION_URL = 'https://bitpay.com'
BITPAY_API_VERSION = '2.0.0'

BITPAY_SUPPORTED_CURRENCIES = (
    'USD', 'EUR', 'GBP', 'CAD', 'AUD', 'NZD', 'CHF', 'JPY',
)


class PaymentProvider(models.Model):
    """BitPay Payment Provider Extension."""

    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('bitpay', "BitPay")],
        ondelete={'bitpay': 'set default'},
    )
    bitpay_pos_token = fields.Char(
        string="BitPay POS Token",
        help="Token generated from the BitPay dashboard under Payment Tools > API Tokens, using the 'pos' facade.",
        groups='base.group_system',
    )

    def _bitpay_get_api_url(self):
        """Return the BitPay API Base URL based on the Provider State."""
        self.ensure_one()
        url = BITPAY_TEST_URL if self.state == 'test' else BITPAY_PRODUCTION_URL
        _logger.debug("BitPay API Base URL selected: %s (State: %s)", url, self.state)
        return url

    def _bitpay_make_request(self, endpoint, payload=None, method='POST'):
        """Execute a Request to the BitPay API and Return the Decoded Response.

        :param str endpoint: The BitPay API resource endpoint.
        :param dict payload: The JSON payload to send in the request body.
        :param str method: The HTTP method (GET, POST, etc.).
        :return: Decoded JSON response dictionary or list.
        :rtype: dict or list
        """
        self.ensure_one()
        if not self.bitpay_pos_token:
            _logger.error("BitPay POS Token is missing in provider configuration.")
            raise ValidationError(_("BitPay POS Token is missing. Please configure it in Provider settings."))

        base_url = self._bitpay_get_api_url().rstrip('/')
        endpoint_clean = f"/{endpoint.lstrip('/')}" if endpoint else ""
        url = f'{base_url}{endpoint_clean}'
        headers = {
            'Content-Type': 'application/json',
            'X-Accept-Version': BITPAY_API_VERSION,
        }

        _logger.info("Sending %s request to BitPay endpoint: %s", method, url)

        try:
            response = requests.request(
                method, url, json=payload, headers=headers, timeout=10,
            )
            _logger.debug("BitPay response status code: %s", response.status_code)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            _logger.exception("BitPay API HTTP Error %s for URL %s", err.response.status_code, url)
            if err.response.status_code == 401:
                raise ValidationError(_(
                    "BitPay authentication failed (401 Unauthorized). "
                    "Please verify your POS Token and ensure Provider State matches the token environment."
                )) from err
            try:
                err_json = err.response.json()
                err_msg = err_json.get('error') or err_json.get('message') or str(err)
            except Exception:
                err_msg = str(err)
            raise ValidationError(_("BitPay API Error: %s", err_msg)) from err
        except RequestException as err:
            _logger.exception("Unable to reach BitPay endpoint: %s", url)
            raise ValidationError(_("BitPay: Could not establish communication with the API. Reason: %s", str(err))) from err

        response_data = response.json()
        if isinstance(response_data, dict) and response_data.get('error'):
            _logger.warning("BitPay API returned an error: %s", response_data['error'])
            raise ValidationError(_(
                "BitPay API returned an error: %s.", response_data['error']
            ))
        return response_data.get('data', response_data) if isinstance(response_data, dict) else response_data

    def _get_supported_currencies(self):
        """Restrict Supported Currencies to Accepted BitPay Fiat Price Currencies."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'bitpay':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in BITPAY_SUPPORTED_CURRENCIES
            )
        return supported_currencies

    def _get_default_payment_method_codes(self):
        """Return the Default Payment Method Codes for BitPay Provider."""
        self.ensure_one()
        if self.code != 'bitpay':
            return super()._get_default_payment_method_codes()
        return ['bitpay']

    def _get_redirect_form_view(self, is_validation=False):
        """Return BitPay Dedicated Redirect Form View."""
        self.ensure_one()
        if self.code != 'bitpay':
            return super()._get_redirect_form_view(is_validation=is_validation)
        return self.redirect_form_view_id or self.env.ref('bitpay_payment_gateway.redirect_form')
