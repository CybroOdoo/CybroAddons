# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from werkzeug import urls
from odoo import api, models, _
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_paytabs_odoo.controllers.payment_paytabs_odoo import PaymentPaytabs

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """
       Inherit the payment transactions, to add Paytabs specific functionality.

       Methods:
           _compute_reference: Override of `payment` to ensure that APS'
       requirements for references are satisfied.
       _get_specific_rendering_values: Override of
       `_get_specific_rendering_values` to handle specific rendering values
       for Paytabs.
       execute_payment: Fetching data and Executing Payment.
       _get_tx_from_notification_data: Get payment status from Paytabs.

       _handle_notification_data: Handle the notification data received
       from Paytabs.

       _process_notification_data: Process the notification data received
       from Paytabs.
       """
    _inherit = 'payment.transaction'

    @api.model
    def _compute_reference(self, provider_code, prefix=None, separator='-',
                           **kwargs):
        """ Override of `payment` to ensure that APS' requirements for
        references are satisfied.

        APS' requirements for transaction are as follows: - References can
        only be made of alphanumeric characters and/or '-' and '_'. The
        prefix is generated with 'tx' as default. This prevents the prefix
        from being generated based on document names that may contain
        non-allowed characters (eg: INV/2020/...).

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
        """ Override of `_get_specific_rendering_values` to handle specific
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
        api_url = self.env['payment.provider'].search(
            [('code', '=', 'paytabs')]).domain
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        sale_order = self.env['payment.transaction'].search(
            [('id', '=', self.id)]).sale_order_ids
        paytabs_values = {
            "profile_id": int(self.provider_id.profile_key),
            "tran_type": "sale",
            "tran_class": "ecom",
            "cart_description": self.reference,
            "cart_id": self.reference,
            "cart_currency": self.currency_id.name,
            "cart_amount": (self.amount - sale_order.amount_tax),
            'return': urls.url_join(base_url,
                                    PaymentPaytabs._return_url),
            'callback': urls.url_join(base_url,
                                      PaymentPaytabs._return_url),
            "api_url": api_url,
            "customer_details": {
                "name": self.partner_name,
                "email": self.partner_email,
                "street1": self.partner_address,
                "city": self.partner_city,
                "state": self.partner_state_id.code,
                "country": self.partner_country_id.code,
                "zip": self.partner_zip
            },
            "shipping_details": {
                "name": self.partner_name,
                "email": self.partner_email,
                "street1": self.partner_address,
                "city": self.partner_city,
                "state": self.partner_state_id.code,
                "country": self.partner_country_id.code,
                "zip": self.partner_zip
            },
        }
        response_content = self.provider_id._paytabs_make_request(
            api_url, paytabs_values)
        response_content['api_url'] = response_content.get('redirect_url')
        return response_content

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """
        Get payment status from Paytabs.

        :param provider_code: The code of the provider handling the transaction.
        :param notification_data: The data received from Paytabs notification.
        :return: The transaction matching the reference.
        """
        tx = super()._get_tx_from_notification_data(provider_code,
                                                    notification_data)
        if provider_code != 'paytabs':
            return tx
        reference = notification_data.get('cartId', False)
        if not reference:
            raise ValidationError(_("PayTabs: No reference found."))
        tx = self.search(
            [('reference', '=', reference), ('provider_code', '=', 'paytabs')])
        if not tx:
            raise ValidationError(
                _("PayTabs: No transaction found matching reference"
                  "%s.") % reference)
        return tx

    def _handle_notification_data(self, provider_code, notification_data):
        """
        Handle the notification data received from Paytabs.

        This method retrieves the transaction corresponding to the
        notification data, processes the notification data, and executes the
        callback.

        :param provider_code: The code of the provider handling the transaction.
        :param notification_data: The data received from Paytabs notification.
        :return: The transaction object.
        """
        tx = self._get_tx_from_notification_data(provider_code,
                                                 notification_data)
        tx._process_notification_data(notification_data)
        tx._execute_callback()
        return tx

    def _process_notification_data(self, notification_data):
        """
        Process the notification data received from PayTabs.

        This method processes the notification data and updates the payment
        state of the transaction accordingly.

        :param notification_data: The data received from PayTabs notification.
            """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'paytabs':
            return

        status = notification_data.get('respStatus')
        if status == 'A':
            self._set_done(state_message="Authorised")
        elif status == 'APPROVED':
            self._set_pending(state_message="Authorised but on hold for "
                                            "further anti-fraud review")
        elif status in ('E', 'D'):
            self._set_canceled(state_message="Error")
        else:
            _logger.warning("Received unrecognized payment state %s for "
                            "transaction with reference %s",
                            status, self.reference)
            self._set_error("PayTabs: " + _("Invalid payment status."))
