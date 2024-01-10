# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Subina P(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import ast
import logging
import pprint
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentMyFatoorahController(http.Controller):
    """MyFatoorah payment acquirer controller"""
    _return_url = '/payment/myfatoorah/_return_url'

    @http.route('/payment/myfatoorah/response', type='http',
                auth='public', website=True, methods=['POST'], csrf=False,
                save_session=False)
    def myfatoorah_payment_response(self, **data):

        """This route is called to send response for the payment requested."""
        payment_data = ast.literal_eval(data["data"])
        vals = {
            'customer': payment_data["CustomerName"],
            'currency': payment_data["DisplayCurrencyIso"],
            'mobile': payment_data["CustomerMobile"],
            'invoice_amount': payment_data["InvoiceValue"],
            'address': payment_data["CustomerAddress"]["Address"],
            'payment_url': payment_data["PaymentURL"],
        }
        return request.render(
            "myfatoorah_payment_gateway.myfatoorah_payment_gateway_form", vals)

    @http.route(_return_url, type='http', auth='public',
                methods=['GET'])
    def myfatoorah__checkout(self, **data):

        """This route is called to return the url to redirect to the checkout
        page of payment."""

        _logger.info("Received MyFatoorah return data:\n%s",
                     pprint.pformat(data))
        tx_sudo = request.env[
            'payment.transaction'].sudo()._get_tx_from_feedback_data(
            'myfatoorah', data)
        tx_sudo._handle_feedback_data('myfatoorah', data)
        return request.redirect('/payment/status')

    @http.route('/payment/myfatoorah/failed', type='http', auth='user',
                website=True, )
    def payment_failed(self):
        """This route is called to redirect to the payment failed page,
        if the payment is failed."""
        return request.render(
            "myfatoorah_payment_gateway.myfatoorah_payment_gateway_failed_form")
