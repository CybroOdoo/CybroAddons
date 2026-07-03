# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import logging
import requests
from hashlib import sha1
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    """Inherit Payment Provider to add new payment into the Payment Provider
     page.
     Methods:
         _get_payment_method_information: Override to add PayPlug payment
         method information to the existing methods.
         _payplug_make_request: Create a request to PayPlug
    """
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('payplug', 'PayPlug')],
        ondelete={'payplug': 'set default'},
        help="Select 'PayPlug' to configure this payment method.")
    payplug_end_point = fields.Char(string="Pay Plug End Point", required=True,
                                    help="Specify the API endpoint provided by PayPlug. This is typically the URL used to interact with the PayPlug payment system.")
    payplug_secret_key = fields.Char(string="Pay Plug Secret Key",
                                     required=True,help="Enter the secret key provided by PayPlug. This key is used to authenticate API requests.")

    @api.model
    def _get_payment_method_information(self):
        """Override to add PayPlug payment method information to the
        existing methods.
        """
        res = super()._get_payment_method_information()
        res['payplug'] = {'mode': 'unique', 'domain': [('type', '=', 'bank')]}
        return res

    def _payplug_make_request(self, url, data=None, method='POST'):
        """Create a request to PayPlug
        :param url: The URL for the request.
        :param data: The data to be sent with the request.
        :param method: The HTTP method for the request (default is 'POST').
        :return: The response content."""
        self.ensure_one()
        try:
            response = requests.request(
                method, url, json=data,
                headers={
                    "Authorization": f'Bearer {self.payplug_secret_key}',
                    "Content-Type": "application/json",
                },
                timeout=60)
            response_content = response.json()
            return response_content
        except requests.exceptions.RequestException:
            _logger.exception("Unable to communicate with PayPlug: %s", url)
            raise ValidationError(
                _("PayPlug: Could not establish a connection to the API."))

    def _playplug_generate_digital_sign(self, values):
        """Create a digital signature for the transaction
        :param values: The values required for generating the digital signature.
        :return: The digital signature."""
        keys = "reference customer_name customer_postcode".split()

        def get_value(key):
            if values.get(key):
                return values[key]
            return ''

        values = dict(values or {})
        sign = ''.join('%s=%s' % (k, get_value(k)) for k in keys)
        shasign = sha1(sign.encode('utf-8')).hexdigest()
        return shasign
