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
from urllib.parse import urljoin
from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_paytabs_odoo.controllers.payment_paytabs_odoo import (
    PaymentPaytabs,
)

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Add PayTabs-specific behavior to payment transactions."""
    _inherit = 'payment.transaction'

    @api.model
    def _compute_reference(self, provider_code, prefix=None, separator='-',
                           **kwargs):
        """Override of `payment` to ensure that PayTabs requirements for
        references are satisfied.

        PayTabs references can only contain alphanumeric characters, hyphens,
        and underscores. The prefix is generated with 'tx' as default. This
        prevents the prefix from being generated based on document names that
        may contain non-allowed characters (eg: INV/2020/...).

        :param str provider_code: The code of the provider handling the
        transaction.
        :param str prefix: The custom prefix used to compute the
        full reference.
        :param str separator: The custom separator used to separate the prefix
        from the suffix.
        :return: The unique reference
        for the transaction.
        :rtype: str
        """
        if provider_code == 'paytabs':
            prefix = payment_utils.singularize_reference_prefix()
        return super()._compute_reference(provider_code, prefix=prefix,
                                          separator=separator, **kwargs)

    def _get_specific_rendering_values(self, processing_values):
        """Override of `_get_specific_rendering_values` to handle specific
        rendering values for PayTabs.

        :param processing_values: The processing values dictionary.
        :return: The rendering values."""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'paytabs':
            return res
        return self.execute_payment()

    def execute_payment(self):
        """Fetching data and Executing Payment
        :return: The response content."""
        # Use self.provider_id directly; it is already the correct singleton
        # provider for this transaction, avoiding an 'Expected singleton' error
        # that occurs when multiple paytabs providers exist in the database.
        api_url = self.provider_id.domain
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        profile_key = self.provider_id.profile_key
        if not profile_key or not profile_key.isdigit():
            raise ValidationError(_(
                "PayTabs Profile ID must be numeric. Please enter the Profile "
                "ID from your PayTabs account, not an email address."
            ))
        paytabs_values = {
            "profile_id": int(profile_key),
            "tran_type": "sale",
            "tran_class": "ecom",
            "cart_description": self.reference,
            "cart_id": self.reference,
            "cart_currency": self.currency_id.name,
            "cart_amount": self.amount,
            'return': urljoin(base_url,
                              f"{PaymentPaytabs._return_url}?ref={self.reference}"),
            'callback': urljoin(base_url,
                                PaymentPaytabs._webhook_url),
            "api_url": api_url,
            "customer_details": {
                "name": self.partner_name,
                "email": self.partner_email,
                "street1": self.partner_address,
                "city": self.partner_city,
                "state": self.partner_state_id.code or "",
                "country": self.partner_country_id.code or "",
                "zip": self.partner_zip or ""
            },
            "shipping_details": {
                "name": self.partner_name,
                "email": self.partner_email,
                "street1": self.partner_address,
                "city": self.partner_city,
                "state": self.partner_state_id.code or "",
                "country": self.partner_country_id.code or "",
                "zip": self.partner_zip or ""
            },
        }
        response_content = self.provider_id._paytabs_make_request(
            api_url, paytabs_values, expect_redirect=True)
        response_content['api_url'] = response_content.get('redirect_url')
        if 'tran_ref' in response_content:
            self.sudo().write({'provider_reference': response_content['tran_ref']})
        _logger.info("PayTabs execute_payment response: %s", response_content)
        return response_content

    @api.model
    def _extract_reference(self, provider_code, payment_data):
        """
        Override of `payment` to extract the transaction reference from
        PayTabs payment data.

        :param str provider_code: The code of the provider handling the transaction.
        :param dict payment_data: The payment data sent by PayTabs.
        :return: The transaction reference, or None if not found.
        :rtype: str|None
        """
        if provider_code != 'paytabs':
            return super()._extract_reference(provider_code, payment_data)

        # Support redirect (cartId), webhook (cart_id), and custom return query (ref) keys
        reference = payment_data.get('cartId') or payment_data.get('cart_id') or payment_data.get('ref')
        if not reference:
            # Return None so the base _process() skips gracefully instead of
            # raising a 422 error on test pings or incomplete callbacks.
            _logger.warning("PayTabs: No reference found in payment data: %s", payment_data)
            return None
        return reference

    def _extract_amount_data(self, payment_data):
        """
        Override of `payment` to skip amount validation for PayTabs.

        The base class returns an empty dict `{}` by default, which causes
        a KeyError in `_validate_amount`. Returning `None` tells Odoo 19 to
        opt out of amount validation entirely for this provider.

        :param dict payment_data: The payment data sent by PayTabs.
        :return: None to skip amount validation.
        """
        if self.provider_code != 'paytabs':
            return super()._extract_amount_data(payment_data)
        return None

    def _apply_updates(self, payment_data):
        """
        Override of `payment` to update the PayTabs transaction state from
        the notification data.

        :param dict payment_data: The payment data sent by PayTabs.
        :return: None
        """
        super()._apply_updates(payment_data)
        if self.provider_code != 'paytabs':
            return

        # Support both form redirect and JSON webhook structures
        status = payment_data.get('respStatus')
        if not status and 'payment_result' in payment_data:
            status = payment_data['payment_result'].get('response_status')

        # If status is missing (e.g. GET browser redirect), query PayTabs API
        if not status:
            _logger.info("PayTabs: Status not in payment data. Querying PayTabs API for transaction: %s",
                         self.reference)
            if self.provider_reference:
                domain = self.provider_id.domain or "https://secure.paytabs.com/payment/query"
                from urllib.parse import urlparse
                parsed_url = urlparse(domain)
                query_url = f"{parsed_url.scheme}://{parsed_url.netloc}/payment/query"

                query_data = {
                    "profile_id": int(self.provider_id.profile_key),
                    "tran_ref": self.provider_reference,
                }
                try:
                    response_content = self.provider_id._paytabs_make_request(
                        query_url, query_data, expect_redirect=False)
                    _logger.info("PayTabs query response for %s: %s", self.reference, response_content)
                    status = response_content.get('payment_result', {}).get('response_status')
                    payment_data.update(response_content)
                except Exception as exc:
                    _logger.error("PayTabs: Failed to query transaction status: %s", exc)

        if status in ('A', 'Authorized'):
            self._set_done(state_message="Authorised")
        elif status in ('APPROVED', 'H', 'Hold', 'P', 'Pending'):
            self._set_pending(
                state_message="Authorised but on hold for further anti-fraud review")
        elif status in ('C', 'E', 'D', 'Declined', 'Error'):
            self._set_canceled(state_message="Error")

        else:
            _logger.warning(
                "Received unrecognized payment state %s for transaction with reference %s",
                status, self.reference)
            self._set_error("PayTabs: " + _("Invalid payment status."))
