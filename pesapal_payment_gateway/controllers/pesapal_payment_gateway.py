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
import ast
import logging
import pprint

from werkzeug.utils import redirect

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentPesapalController(http.Controller):
    """ Instance for the pesapal payment controller """

    @http.route('/payment/pesapal/response', type='http', auth='public',
                website=True, methods=['POST'], csrf=False, save_session=False)
    def pesapal_payment_response(self, **data):
        """Function to get the payment response"""
        payment_data = ast.literal_eval(data["data"])
        redirect_url = payment_data.get("redirect_url")
        if not redirect_url:
            _logger.error("Pesapal: missing redirect_url in payment data: %s",
                          payment_data)
            return redirect('/payment/status')
        return redirect(redirect_url)

    @http.route('/payment/pesapal/_return_url', type='http', auth='public',
                website=True, methods=['GET'], csrf=False, save_session=False)
    def pesapal_checkout(self, **data):
        """Handle Pesapal callback: both browser redirect and IPN notification.

        Pesapal sends OrderTrackingId, OrderMerchantReference, and
        OrderNotificationType as GET query parameters.
        """
        _logger.info("Received Pesapal return data:\n%s",
                     pprint.pformat(data))

        try:
            tx_sudo = request.env['payment.transaction'].sudo()
            tx_sudo._handle_notification_data('pesapal', data)
        except Exception:
            _logger.exception("Pesapal callback processing failed.")
            raise

        return request.redirect('/payment/status')

    @http.route('/payment/pesapal/failed', type='http', auth='user',
                website=True, )
    def payment_failed(self):
        """ Function to render the payment failed cases"""
        return request.render(
            "pesapal_payment_gateway.pesapal_payment_gateway_failed_form")