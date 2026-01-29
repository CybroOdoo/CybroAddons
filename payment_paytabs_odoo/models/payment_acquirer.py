# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

SUPPORTED_CURRENCIES = ('EGP', 'USD', 'EUR', 'GBP', 'INR')


class PaymentAcquirer(models.Model):
    """The Class PaymentAcquirerPaytabs represents a list of fields
    that can be used to create a new payment method as a paytab."""
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[
        ('paytabs', 'Paytabs')
    ], ondelete={'paytabs': 'set default'})
    profile_id = fields.Char(string='Profile ID', groups='base.group_user',
                             help="Paytabs profile id of a user")
    api_key = fields.Char(string='Api Key', required_if_provider='paytabs',
                          groups='base.group_user', help="Paytabs API key")
    domain = fields.Char(string='Domain', help='Domain for the url')

    @api.model
    def _get_compatible_acquirers(self, *args, currency_id=None, **kwargs):
        """Returns the compatible acquires"""
        acquirers = super()._get_compatible_acquirers(*args,
                                                      currency_id=currency_id,
                                                      **kwargs)
        currency = self.env['res.currency'].browse(currency_id).exists()
        if currency and currency.name not in SUPPORTED_CURRENCIES:
            acquirers = acquirers.filtered(lambda a: a.provider != 'paytabs')
        return acquirers

    def _get_default_payment_method_id(self):
        """Check the default payment method and if the provider is not
        the paytab then it returns the function else it call
         the id of the paytab """
        self.ensure_one()
        if self.provider != 'paytabs':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment_paytabs_odoo.payment_method_paytabs').id

    def _paytabs_make_request(self, url, data=None, method='POST'):
        """Create a request to paytabs """
        self.ensure_one()
        data.pop('api_url')
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(method, url, json=data,
                                        headers=headers,
                                        timeout=60)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            _logger.exception("Unable to communicate with Paytabs: %s", url)
            raise ValidationError("Paytabs: " + _(
                "Could not establish the connection to the API."))
        return response.json()
