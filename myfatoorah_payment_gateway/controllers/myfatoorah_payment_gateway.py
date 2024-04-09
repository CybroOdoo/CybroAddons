# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina (odoo@cybrosys.com)
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
from odoo import http
from odoo.http import request
import ast

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
        return request.render(
            "myfatoorah_payment_gateway.myfatoorah_payment_gateway_form", vals)

    @http.route(_return_url, type='http', auth='public',
                methods=['GET'])
    def myfatoorah_checkout(self, **data):
        """ Function to redirect to the payment checkout"""
        _logger.info("Received MyFatoorah return data:\n%s",
                     pprint.pformat(data))
        tx_sudo = request.env[
            'payment.transaction'].sudo()._get_tx_from_notification_data(
            'myfatoorah', data)
        tx_sudo._handle_notification_data('myfatoorah', data)
        return request.redirect('/payment/status')

    @http.route('/payment/myfatoorah/failed', type='http', auth='user',
                website=True, )
    def payment_failed(self):
        """ Function to render the payment failed cases"""
        return request.render(
            "myfatoorah_payment_gateway.myfatoorah_payment_gateway_failed_form")
