# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentPaytabs(http.Controller):
    """
    Controller for handling payment-related operations with Paytabs.

    Methods:
        paytabs_return: Handle browser redirect (GET/POST) from PayTabs.
        paytabs_webhook: Handle server-to-server IPN webhook (POST) from PayTabs.
    """
    _return_url = '/payment/paytabs/return'
    _webhook_url = '/payment/paytabs/webhook'

    @http.route(_return_url, type='http', auth='public',
                methods=['GET', 'POST'], csrf=False, save_session=False)
    def paytabs_return(self, **post):
        """Handle the return from the PayTabs payment gateway (browser redirect).

        We process the data (if any) to update the transaction state and then
        forward the user to the Odoo payment-status page.
        """
        _logger.info("PayTabs return received with method %s and data: %s", request.httprequest.method, post)

        # In case the browser POST includes JSON data in the body
        if request.httprequest.method == 'POST' and not post:
            try:
                data = json.loads(request.httprequest.data)
                if isinstance(data, dict):
                    post.update(data)
            except Exception:
                _logger.exception("PayTabs: Failed to parse return JSON data.")

        if post:
            request.env['payment.transaction'].sudo()._process(
                'paytabs', post)

        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='http', auth='public',
                methods=['POST'], csrf=False, save_session=False)
    def paytabs_webhook(self, **post):
        """Handle server-to-server IPN notifications from PayTabs."""
        _logger.info("PayTabs IPN webhook received with data: %s", post)

        if not post:
            try:
                data = json.loads(request.httprequest.data)
                if isinstance(data, dict):
                    post.update(data)
            except Exception:
                _logger.exception("PayTabs: Failed to parse webhook JSON payload.")

        if post:
            request.env['payment.transaction'].sudo()._process(
                'paytabs', post)

        return request.make_response('OK', [('Content-Type', 'text/plain')])
