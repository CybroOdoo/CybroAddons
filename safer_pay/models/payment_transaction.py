# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
import logging
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Create a new records for safer_pay in payment transaction """
    _inherit = 'payment.transaction'

    capture_manually = fields.Boolean(related='provider_id.capture_manually')

    # === ACTION METHODS ===#

    def action_saferpay_set_done(self):
        """ Set the state of the safer_pay transaction to 'done'.
        Note: self.ensure_one()
        :return: None
        """
        self.ensure_one()
        if self.provider_code != 'saferpay':
            return
        notification_data = {'reference': self.reference,
                             'simulated_state': 'done'}
        self._handle_notification_data('saferpay', notification_data)

    def action_saferpay_set_canceled(self):
        """ Set the state of the saferpay transaction to 'cancel'.
        Note: self.ensure_one()
        :return: None
        """
        self.ensure_one()
        if self.provider_code != 'saferpay':
            return
        notification_data = {'reference': self.reference,
                             'simulated_state': 'cancel'}
        self._handle_notification_data('saferpay', notification_data)

    def action_saferpay_set_error(self):
        """ Set the state of the demo transaction to 'error'.
        Note: self.ensure_one()
        :return: None
        """
        self.ensure_one()
        if self.provider_code != 'saferpay':
            return
        notification_data = {'reference': self.reference,
                             'simulated_state': 'error'}
        self._handle_notification_data('saferpay', notification_data)

    # === BUSINESS METHODS ===#

    def _send_payment_request(self):
        """ Override of payment to simulate a payment request.
        Note: self.ensure_one()
        :return: None
        """
        super()._send_payment_request()
        if self.provider_code != 'saferpay':
            return

        if not self.token_id:
            raise UserError("saferpay: " + _("The transaction is not "
                                             "linked to a token."))
        simulated_state = self.token_id.saferpay_simulated_state
        notification_data = {'reference': self.reference,
                             'simulated_state': simulated_state}
        self._handle_notification_data('saferpay', notification_data)

    def _send_refund_request(self, **kwargs):
        """ Override of payment to simulate a refund.

        Note: self.ensure_one()

        :param dict kwargs: The keyword arguments.
        :return: The refund transaction created to process the refund request.
        :rtype: recordset of `payment.transaction`
        """
        refund_tx = super()._send_refund_request(**kwargs)
        if self.provider_code != 'saferpay':
            return refund_tx
        notification_data = {'reference': refund_tx.reference,
                             'simulated_state': 'done'}
        refund_tx._handle_notification_data('saferpay', notification_data)

        return refund_tx

    def _send_capture_request(self, amount_to_capture=None):
        """ Override of `payment` to simulate a capture request. """
        child_capture_tx = super()._send_capture_request(amount_to_capture=
                                                         amount_to_capture)
        if self.provider_code != 'saferpay':
            return child_capture_tx

        tx = child_capture_tx or self
        notification_data = {
            'reference': tx.reference,
            'simulated_state': 'done',
            'manual_capture': True,  # Distinguish manual captures
            # from regular one-step captures.
        }
        tx._handle_notification_data('saferpay', notification_data)

        return child_capture_tx

    def _send_void_request(self, amount_to_void=None):
        """ Override of `payment` to simulate a void request. """
        child_void_tx = super()._send_void_request(amount_to_void=
                                                   amount_to_void)
        if self.provider_code != 'saferpay':
            return child_void_tx

        tx = child_void_tx or self
        notification_data = {'reference': tx.reference,
                             'simulated_state': 'cancel'}
        tx._handle_notification_data('saferpay', notification_data)

        return child_void_tx

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on dummy data.
        :param str provider_code: The code of the provider that handled the
        transaction
        :param dict notification_data: The dummy notification data
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code,
                                                    notification_data)
        if provider_code != 'saferpay' or len(tx) == 1:
            return tx

        reference = notification_data.get('reference')
        tx = self.search([('reference', '=', reference), ('provider_code',
                                                          '=', 'saferpay')])
        if not tx:
            raise ValidationError(
                "saferpay: " + _("No transaction found matching reference %s.",
                                 reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on dummy data.

        Note: self.ensure_one()

        :param dict notification_data: The dummy notification data
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'saferpay':
            return

        # Update the provider reference.
        self.provider_reference = f'saferpay-{self.reference}'

        # Create the token.
        if self.tokenize:
            # The reasons why we immediately tokenize the transaction
            # regardless of the state rather
            # than waiting for the payment method to be validated
            # ('authorized' or 'done') like the
            # other payment providers do are:
            # - To save the simulated state and payment details on the
            # token while we have them.
            # - To allow customers to create tokens whose transactions
            # will always end up in the
            #   said simulated state.
            self._saferpay_tokenize_from_notification_data(notification_data)

        # Update the payment state.
        state = notification_data['simulated_state']
        if state == 'pending':
            self._set_pending()
        elif state == 'done':
            if self.capture_manually and not notification_data.get(
                    'manual_capture'):
                self._set_authorized()
            else:
                self._set_done()
                # Immediately post-process the transaction if it is a refund,
                # as the post-processing
                # will not be triggered by a customer browsing the transaction
                # from the portal.
                if self.operation == 'refund':
                    self.env.ref(
                        'payment.cron_post_process_payment_tx')._trigger()
        elif state == 'cancel':
            self._set_canceled()
        else:  # Simulate an error state.
            self._set_error(
                _("You selected the following demo payment status: %s", state))

    def _saferpay_tokenize_from_notification_data(self, notification_data):
        """ Create a new token based on the notification data.
        Note: self.ensure_one()
        :param dict notification_data: The fake notification data to tokenize
         from.
        :return: None
        """
        self.ensure_one()

        state = notification_data['simulated_state']

        token = self.env['payment.token'].create({
            'provider_id': self.provider_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_details': notification_data['payment_details'],
            'partner_id': self.partner_id.id,
            'provider_ref': 'fake provider reference',
            'saferpay_simulated_state': state,
        })
        self.write({
            'token_id': token,
            'tokenize': False,
        })
        _logger.info(
            "Created token with id %s for partner with id %s.",
            token.id, self.partner_id.id
        )
