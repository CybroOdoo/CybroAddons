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
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import logging
from werkzeug.urls import url_join
from odoo import _, api, models
from odoo.addons.payment.logging import get_payment_logger

_logger = get_payment_logger(__name__)


class PaymentTransaction(models.Model):
    """BitPay Payment Transaction Extension."""

    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """Override of Payment to Compute BitPay Specific Rendering Values.

        :param dict processing_values: Generic processing values.
        :return: BitPay rendering values dictionary.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'bitpay':
            return res

        _logger.info("Creating BitPay Invoice for transaction: %s", self.reference)

        base_url = self.provider_id.get_base_url()
        return_url = url_join(base_url, f'/payment/bitpay/return?ref={self.reference}')
        payload = {
            'token': self.provider_id.bitpay_pos_token,
            'price': self.amount,
            'currency': self.currency_id.name,
            'orderId': self.reference,
            'notificationURL': url_join(base_url, '/payment/bitpay/notification'),
            'redirectURL': return_url,
            'closeURL': return_url,
            'autoRedirect': True,
            'fullNotifications': True,
            'extendedNotifications': True,
            'transactionSpeed': 'medium',
        }

        if self.partner_email:
            payload['buyer'] = {'email': self.partner_email}

        response_data = self.provider_id._bitpay_make_request(
            'invoices', payload=payload, method='POST'
        )

        invoice_id = None
        if isinstance(response_data, dict):
            if isinstance(response_data.get('data'), dict):
                invoice_id = response_data['data'].get('id')
            if not invoice_id:
                invoice_id = response_data.get('id')

        if not invoice_id:
            _logger.error("Failed to retrieve BitPay Invoice ID from response: %s", response_data)
            raise ValueError(_("Could not generate BitPay Invoice."))

        _logger.info("BitPay Invoice Created: %s", invoice_id)

        self.provider_reference = invoice_id
        api_url = self.provider_id._bitpay_get_api_url()
        res.update({
            'api_url': f"{api_url}/invoice",
            'invoice_id': invoice_id,
        })
        return res

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Find the transaction matching notification data.

        :param str provider_code: The code of the provider.
        :param dict notification_data: Notification payload data.
        :return: The transaction matching notification reference.
        :rtype: recordset of 'payment.transaction'
        """
        if provider_code != 'bitpay':
            return super()._get_tx_from_notification_data(provider_code, notification_data)

        reference = self._extract_reference(provider_code, notification_data)
        if not reference:
            _logger.warning("BitPay notification data missing 'orderId': %s", notification_data)
            raise ValueError(_("BitPay: Received data with missing orderId reference."))

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'bitpay')])
        if not tx:
            _logger.warning("BitPay: No transaction found for reference %s", reference)
            raise ValueError(_("BitPay: No transaction found for reference %s", reference))

        return tx

    def _extract_reference(self, provider_code, notification_data):
        """Extract order reference from notification data.

        :param str provider_code: Provider code.
        :param dict notification_data: BitPay payload status data.
        :return: Reference string or None.
        :rtype: str
        """
        if provider_code != 'bitpay':
            return super()._extract_reference(provider_code, notification_data)

        data = notification_data.get('data', notification_data) if isinstance(notification_data, dict) else {}
        if isinstance(data, dict):
            if data.get('orderId'):
                return data.get('orderId')
            if data.get('ref'):
                return data.get('ref')
            if data.get('reference'):
                return data.get('reference')

        if isinstance(notification_data, dict):
            if notification_data.get('orderId'):
                return notification_data.get('orderId')
            if notification_data.get('ref'):
                return notification_data.get('ref')
            if notification_data.get('reference'):
                return notification_data.get('reference')

        return super()._extract_reference(provider_code, notification_data)

    def _extract_amount_data(self, notification_data):
        """Extract amount data from notification payload.

        :param dict notification_data: BitPay payload status data.
        :return: Amount data dictionary containing 'amount' and 'currency_code'.
        :rtype: dict
        """
        if self.provider_code != 'bitpay':
            return super()._extract_amount_data(notification_data)

        data = notification_data.get('data', notification_data) if isinstance(notification_data, dict) else {}
        price = None
        currency_code = None

        if isinstance(data, dict):
            price = data.get('price') or data.get('amount')
            currency_code = data.get('currency') or data.get('currency_code')

        if price is None and isinstance(notification_data, dict):
            price = notification_data.get('price') or notification_data.get('amount')
            currency_code = currency_code or notification_data.get('currency') or notification_data.get('currency_code')

        return {
            'amount': float(price) if price is not None else self.amount,
            'currency_code': currency_code or self.currency_id.name,
        }

    def _apply_updates(self, payment_data):
        """Update transaction state based on BitPay payment notification data.

        :param dict payment_data: BitPay notification data dictionary.
        """
        if self.provider_code != 'bitpay':
            return super()._apply_updates(payment_data)

        self._process_notification_data(payment_data)

    def _process_notification_data(self, notification_data):
        """Process BitPay notification data and update transaction status.

        :param dict notification_data: BitPay payload status data.
        """
        if self.provider_code != 'bitpay':
            return

        data = notification_data.get('data', notification_data) if isinstance(notification_data, dict) else {}
        status = data.get('status') if isinstance(data, dict) else None
        if not status and isinstance(notification_data, dict):
            status = notification_data.get('status')

        _logger.info("Processing BitPay status update for %s: '%s'", self.reference, status)

        if status in ['paid', 'confirmed', 'complete']:
            self._set_done()
        elif status in ['expired', 'invalid']:
            self._set_canceled()
        elif status in ['new']:
            self._set_pending()
        else:
            _logger.warning("Unhandled BitPay status '%s' for transaction %s", status, self.reference)

    def _bitpay_sync_live_invoice_status(self):
        """Fetch live invoice status from BitPay REST API for pending transactions."""

        self.ensure_one()
        if self.provider_code != 'bitpay' or not self.provider_id.bitpay_pos_token:
            return

        _logger.info(
            "[BITPAY STATUS POLL] Transaction %s in state '%s'. Polling live status from BitPay API...",
            self.reference,
            self.state,
        )

        try:
            if self.provider_reference:
                endpoint = f"invoices/{self.provider_reference}?token={self.provider_id.bitpay_pos_token}"
            else:
                endpoint = f"invoices?token={self.provider_id.bitpay_pos_token}&orderId={self.reference}"

            response_data = self.provider_id._bitpay_make_request(endpoint, method='GET')
            
            latest_invoice = None
            if isinstance(response_data, dict):
                if isinstance(response_data.get('data'), dict):
                    latest_invoice = response_data['data']
                elif isinstance(response_data.get('data'), list) and response_data['data']:
                    latest_invoice = response_data['data'][0]
                elif response_data.get('status'):
                    latest_invoice = response_data

            if latest_invoice and isinstance(latest_invoice, dict):
                live_status = latest_invoice.get('status')
                _logger.info(
                    "[BITPAY LIVE SYNC] Received live status '%s' for transaction %s (Invoice ID: %s)",
                    live_status,
                    self.reference,
                    latest_invoice.get('id'),
                )
                if live_status:
                    self._process_notification_data({'data': latest_invoice})
            else:
                _logger.warning(
                    "[BITPAY LIVE SYNC] No valid invoice data returned from BitPay for transaction %s",
                    self.reference,
                )
        except Exception as err:
            _logger.warning(
                "[BITPAY LIVE SYNC] Failed to sync status from BitPay API for %s: %s",
                self.reference,
                err,
            )
