# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    """    Inherit Payment Provider to add new payment into the Payment Provider
     page.
     Methods:
         _get_payment_method_information: Override to add PayTabs payment
         method information to the existing methods.
         _paytabs_make_request: Create a request to PayTabs
         """
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('paytabs', 'paytabs')],
                            ondelete={'paytabs': 'set default'},
                            help="The technical code of this payment provider",
                            string="Code")
    profile_key = fields.Char(string='Profile ID', groups='base.group_user',
                              help="PayTabs profile id of the user")
    api_key = fields.Char(string='Api Key', required_if_provider='paytabs',
                          groups='base.group_user', help="PayTabs Server key")
    domain = fields.Char(string='Api endpoint', help='API endpoint of Paytabs')

    @api.model
    def _get_payment_method_information(self):
        """Override to add PayTabs payment method information to the
        existing methods.
        """
        res = super()._get_payment_method_information() if hasattr(super(), '_get_payment_method_information') else {}
        res['paytabs'] = {'mode': 'unique', 'domain': [('type', '=', 'bank')]}
        return res

    def _paytabs_make_request(self, url, data=None, method='POST', expect_redirect=False):
        """Create a request to PayTabs
        :param url: The URL for the request.
        :param data: The data to be sent with the request.
        :param method: The HTTP method for the request (default is 'POST').
        :param expect_redirect: Boolean indicating if a redirect_url is expected in the response.
        :return: The response content."""
        self.ensure_one()
        if data and 'api_url' in data:
            data.pop('api_url')
        try:
            response = requests.request(
                method, url, json=data,
                headers={
                    "Authorization": self.api_key,
                    "Content-Type": "application/json",
                },
                timeout=60)
            response_content = response.json()
            if 'code' in response_content:
                code = response_content['code']
                message = response_content.get('message', '')
                if code == 1:
                    raise ValidationError(
                        _("PayTabs: Check profile ID and Api Key"))
                elif code == 206:
                    raise ValidationError(_("PayTabs: Currency not available."))
                elif code == 210:
                    raise ValidationError(_(
                        "PayTabs Error (Code 210): Invalid Callback URL (%s). "
                        "PayTabs requires a publicly accessible HTTPS callback URL. "
                        "'localhost' and HTTP URLs are not allowed by PayTabs. "
                        "Please set 'web.base.url' in Odoo System Parameters to a valid HTTPS URL (e.g., using ngrok)."
                    ) % message)
                else:
                    raise ValidationError(
                        _("PayTabs API Error (Code %s): %s", code, message)
                    )
            if expect_redirect and 'redirect_url' not in response_content:
                raise ValidationError(
                    _("PayTabs: Invalid response received from PayTabs API.")
                )
            return response_content
        except requests.exceptions.RequestException as exc:
            _logger.exception("Unable to communicate with Paytabs: %s", url)
            raise ValidationError(
                _("PayTabs: Could not establish a connection to the API.")
            ) from exc
