# -*- coding: utf-8 -*-
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
import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    """Inherit Payment Provider to add new payment into the Payment Provider
     page.

     Methods:
         _get_payment_method_information: Override to add Network International payment
         method information to the existing methods.
         _get_authentication_token: Create an Auth token for Network international order
    """
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('network_international', 'Network International')],
        ondelete={'network_international': 'set default'}
    )
    api_key = fields.Char(string="Key Id",
                          help="This is the API Key used to authenticate with the payment gateway.",required=True)
    outlet_reference = fields.Char(string="Outlet Reference",
                                   help="This is the unique reference for the outlet in the payment gateway.",required=True)
    auth_token = fields.Char(string="Auth Token",
                             help="This token is used to authenticate API requests to the payment gateway.",required=True)
    api_endpoint = fields.Char(string="API Endpoint",help="URL of the API endpoint where requests will be sent",required=True)

    @api.model
    def _get_payment_method_information(self):
        """Override to add Network International payment method information to the
        existing methods.
        """
        res = super()._get_payment_method_information()
        res['network_international'] = {'mode': 'unique',
                                        'domain': [('type', '=', 'bank')]}
        return res

    def _get_authentication_token(self, url, data=None, method='POST'):
        """Function to create an Authentication token for Network International payments.

        :param url: The URL for the request.
        :param data: The data to be sent with the request.
        :param method: The HTTP method for the request (default is 'POST').
        :return: The response content."""
        self.ensure_one()
        try:
            response = requests.request(
                method, url, json=data,
                headers={
                    "Content-Type": "application/vnd.ni-identity.v1+json",
                    "Authorization": f'Basic {self.api_key}'
                },
                timeout=60)
            response_content = response.json()
            return response_content
        except requests.exceptions.RequestException:
            _logger.exception(
                "Unable to Generate Auth Token for Network International: %s",
                url)
            raise ValidationError(
                _("Network International: Could not establish a connection to the API."))

    def _network_international_make_request(self, url, auth_token, data=None,
                                            method='POST'):
        """Create a payment request to Network International.

        :param url: The URL for the request.
        :param auth_token: The Authentication token used for payment verification.
        :param data: The data to be sent with the request.
        :param method: The HTTP method for the request (default is 'POST').
        :return: The response content."""
        self.ensure_one()
        try:
            response = requests.request(
                method, url, json=data,
                headers={
                    "Authorization": f'Bearer {auth_token}',
                    "Content-Type": "application/vnd.ni-payment.v2+json",
                    "Accept": "application/vnd.ni-payment.v2+json"
                },
                timeout=60)
            if not response.ok:
                _logger.error("Network International API Error: %s", response.text)
                raise ValidationError(f"Network International API Error: {response.text}")
            response_content = response.json()
            return response_content
        except requests.exceptions.RequestException:
            _logger.exception(
                "Unable to communicate with Network International: %s", url)
            raise ValidationError(
                _("Network International: Could not establish a connection to the API."))
