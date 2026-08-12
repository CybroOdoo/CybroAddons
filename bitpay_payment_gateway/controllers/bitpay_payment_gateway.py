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
import json
import logging
from odoo import http
from odoo.http import request
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing

_logger = logging.getLogger(__name__)


class BitPayController(http.Controller):
    """BitPay Controller for Notification Webhooks and Return URLs."""

    _notification_url = '/payment/bitpay/notification'
    _return_url = '/payment/bitpay/return'

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def bitpay_return(self, **data):
        """Process Customer Return from BitPay Checkout and Redirect to Status Page.

        :param dict data: Return parameters passed in query string or form data.
        :return: HTTP Response redirecting to /payment/status.
        """
        _logger.info("Customer returned from BitPay checkout with data: %s", data)
        tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference('bitpay', data)
        if tx_sudo:
            if tx_sudo.state in ('draft', 'pending'):
                _logger.info("Transaction %s is in %s state. Syncing live status from BitPay API.", tx_sudo.reference, tx_sudo.state)
                tx_sudo._bitpay_sync_live_invoice_status()
        else:
            _logger.warning("Could not find matching transaction for return data: %s", data)
        return request.redirect('/payment/status')

    @http.route(_notification_url, type='http', auth='public', methods=['POST'], csrf=False)
    def bitpay_notification(self, **data):
        """Process BitPay IPN (Instant Payment Notification) Webhook.

        :param dict data: Notification data passed in query string or form data.
        :return: HTTP String response 'OK' or error code.
        """
        _logger.info("Received HTTP POST webhook at %s", self._notification_url)
        raw_body = request.httprequest.data.decode('utf-8') if request.httprequest.data else ''
        try:
            notification_data = json.loads(raw_body) if raw_body else data
        except json.JSONDecodeError:
            notification_data = data

        tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference('bitpay', notification_data)
        if not tx_sudo:
            _logger.warning("Could not find matching Odoo transaction for notification payload.")
            return 'TRANSACTION_NOT_FOUND'

        _logger.info("Processing notification for transaction %s (State: %s)", tx_sudo.reference, tx_sudo.state)
        tx_sudo._process('bitpay', notification_data)
        return 'OK'


class BitPayPaymentPostProcessing(PaymentPostProcessing):
    """Extension of Payment Post Processing Controller to Poll Live BitPay Status."""

    @http.route('/payment/status', type='http', auth='public', website=True, sitemap=False)
    def display_status(self, **kwargs):
        """Sync Live BitPay Invoice Status Before Rendering Payment Status Page.

        :param dict kwargs: Request keyword arguments.
        :return: Rendered status page response.
        """
        monitored_tx = self._get_monitored_transaction()
        if monitored_tx and monitored_tx.provider_code == 'bitpay' and monitored_tx.state in ('draft', 'pending'):
            _logger.info("Syncing live status for monitored transaction %s during display_status.", monitored_tx.reference)
            monitored_tx._bitpay_sync_live_invoice_status()
        return super().display_status(**kwargs)

    @http.route('/payment/status/poll', type='jsonrpc', auth='public')
    def poll_status(self, **kwargs):
        """Sync Live BitPay Invoice Status During Frontend Status Page Polling.

        :param dict kwargs: Request keyword arguments.
        :return: Poll status dictionary response.
        """
        monitored_tx = self._get_monitored_transaction()
        if monitored_tx and monitored_tx.provider_code == 'bitpay' and monitored_tx.state in ('draft', 'pending'):
            _logger.info("Syncing live status for monitored transaction %s during poll_status.", monitored_tx.reference)
            monitored_tx._bitpay_sync_live_invoice_status()
        return super().poll_status(**kwargs)
