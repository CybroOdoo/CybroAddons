# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from pay_ccavenue import CCAvenue
from odoo import api, models, _
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """
       Inherit the payment transactions, to add CCAvenue specific functionality.
       Methods:
        _compute_reference: Override of `payment` to ensure that APS'
       requirements for references are satisfied.
       _get_specific_rendering_values: Override of
       `_get_specific_rendering_values` to handle specific rendering values
       for CCAvenue.
       execute_payment: Fetching data and Executing Payment.
       _get_tx_from_notification_data: Get payment status from CCAvenue.

       _handle_notification_data: Handle the notification data received
       from CCAvenue.

       _process_notification_data: Process the notification data received
       from CCAvenue.
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
        if provider_code == 'avenue':
            prefix = payment_utils.singularize_reference_prefix()
        return super()._compute_reference(provider_code, prefix=prefix,
                                          separator=separator, **kwargs)

    def _get_specific_rendering_values(self, processing_values):
        """ Override of `_get_specific_rendering_values` to handle specific
        rendering values for CCAvenue.

        :param processing_values: The processing values dictionary.
        :return: The rendering values."""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'avenue':
            return res
        return self.execute_payment()

    def execute_payment(self):
        """
        Fetches necessary data and executes the payment using CCAvenue
        :return:
         A dictionary containing the encrypted data, access code, and API URL.
        """
        # Initialize CCAvenue with credentials
        self.ensure_one()
        web_url = self.env['ir.config_parameter'].get_param('web.base.url')
        sale_order = self.env['sale.order'].search(
            [('id', '=', self.sale_order_ids.id)])
        form_data = {
            "order_id": self.reference,
            "currency": self.currency_id.name,
            "amount": (self.amount - sale_order.amount_tax),
            "redirect_url": f"{web_url}/payment/ccavenue/return",
            "cancel_url": f"{web_url}/payment/ccavenue/cancel",
            "billing_name": self.partner_name,
            "billing_tel": self.partner_phone,
            "billing_address": self.partner_address,
            "billing_city": self.partner_city,
            "billing_state": self.partner_state_id.name,
            "billing_country": self.partner_country_id.name,
            "billing_zip": self.partner_zip,
            "billing_email": self.partner_email
        }
        if self.provider_id.state == "test":
            api_url = ("https://test.ccavenue.com/transaction/transaction.do?command=initiateTransaction")
        else:
            api_url = ("https://secure.ccavenue.com/transaction/transaction.do"
                       "?command=initiateTransaction")
        ccavenue = CCAvenue(self.provider_id.working_key,
                            self.provider_id.access_code,
                            self.provider_id.merchant_key,
                            web_url + '/payment/ccavenue/return',
                            web_url + '/payment/ccavenue/cancel')
        encrypted_data = ccavenue.encrypt(form_data)
        response_content = {
            "encrypted_data": encrypted_data,
            "access_code": self.provider_id.access_code,
            "api_url": api_url
        }
        return response_content

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """
        Get payment status from CCAvenue.

        :param provider_code: The code of the provider handling the transaction.
        :param notification_data: The data received from CCAvenue notification.
        :return: The transaction matching the reference.
        """
        tx = super()._get_tx_from_notification_data(provider_code,
                                                    notification_data)
        if provider_code != 'avenue':
            return tx
        reference = notification_data.get('order_id', False)
        if not reference:
            raise ValidationError("CCAvenue: " + _("No reference found.", ))
        tx = self.search(
            [('reference', '=', reference), ('provider_code', '=', 'avenue')])
        if not tx:
            raise ValidationError("CCAvenue: " + _("No transaction found "
                                                   "matching reference %s.",
                                                   reference))
        return tx

    def _handle_notification_data(self, provider_code, notification_data):
        """
        Handle the notification data received from CCAvenue.

        This method retrieves the transaction corresponding to the
        notification data, processes the notification data, and executes the
        callback.

        :param provider_code: The code of the provider handling the transaction.
        :param notification_data: The data received from CCAvenue notification.
        :return: The transaction object.
        """
        tx = self._get_tx_from_notification_data(provider_code,
                                                 notification_data)
        tx._process_notification_data(notification_data)
        tx._execute_callback()
        return tx

    def _process_notification_data(self, notification_data):
        """
        Process the notification data received from CCAvenue.

        This method processes the notification data and updates the payment
        state of the transaction accordingly.

        :param notification_data: The data received from CCAvenue notification.
            """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'avenue':
            return
        status = notification_data.get('order_status')
        if status == 'Success':
            self._set_done()
        elif status == 'Aborted':
            self._set_canceled(state_message="Error")
        elif status == "Failure":
            self._set_canceled(state_message="Error")
        else:
            _logger.warning("received unrecognized payment state %s for "
                            "transaction with reference %s",
                            status, self.reference)
            self._set_error("CCAVENUE: " + _("Invalid payment status."))
