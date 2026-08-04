# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Harshitha AP (odoo@cybrosys.com)
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
import logging
import pprint
import ast

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentMyFatoorahController(http.Controller):
    """ Instance for the myfatoorah controller """

    _return_url = '/payment/myfatoorah/_return_url'

    @http.route('/payment/myfatoorah/response', type='http', auth='public',
                website=True, methods=['POST'], csrf=False, save_session=False)
    def myfatoorah_payment_response(self, **data):
        """Function to get the payment response"""
        payment_data = ast.literal_eval(data["data"])
        vals = {
            'customer': payment_data["CustomerName"],
            'currency': payment_data["DisplayCurrencyIso"],
            'mobile': payment_data["CustomerMobile"],
            'invoice_amount': payment_data["InvoiceValue"],
            'address': payment_data["CustomerAddress"]["Address"],
            'payment_url': payment_data["InvoiceURL"],
        }
        return request.render("myfatoorah_payment_gateway.myfatoorah_payment_gateway_form", vals)

    @http.route(_return_url, type='http', auth='public', methods=['GET'])
    def myfatoorah_checkout(self, **data):
        """ Function to redirect to the payment checkout"""
        _logger.info("Received MyFatoorah return data:\n%s",
                     pprint.pformat(data))
        # `data` only contains 'paymentId'/'Id' query params from the return
        # URL. Odoo 19's payment.transaction._process() needs the full
        # payment payload (CustomerReference, InvoiceStatus, InvoiceValue,
        # ...), so we look that up from MyFatoorah's GetPaymentStatus
        # endpoint first, then hand the result to _process().
        payment_id = data.get('paymentId') or data.get('Id')
        provider_sudo = request.env['payment.provider'].sudo().search(
            [('code', '=', 'myfatoorah')], limit=1)
        if payment_id and provider_sudo:
            payment_data = provider_sudo._myfatoorah_get_payment_status(
                payment_id)
            request.env['payment.transaction'].sudo()._process(
                'myfatoorah', payment_data)
        else:
            _logger.warning(
                "MyFatoorah return URL called without a paymentId, or no "
                "MyFatoorah provider is configured.")
        return request.redirect('/payment/status')

    @http.route('/payment/myfatoorah/failed', type='http', auth='user',
                website=True)
    def payment_failed(self):
        """ Function to render the payment failed cases"""
        return request.render(
            "myfatoorah_payment_gateway.myfatoorah_payment_gateway_failed_form")