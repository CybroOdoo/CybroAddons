#############################################################################
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
# pylint: disable=missing-module-docstring,protected-access,import-error,no-name-in-module,unused-argument
import ast
import logging
import pprint

from odoo import http
from odoo.http import request

from odoo.addons.payment.controllers.payment_status import PaymentStatus

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

    @http.route(_return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def myfatoorah_checkout(self, **data):
        """ Function to redirect to the payment checkout"""
        _logger.info("Received MyFatoorah return data:\n%s",
                     pprint.pformat(data))
        # `data` only contains 'paymentId'/'Id' query params from the return
        # URL. We look up the full payment payload (CustomerReference,
        # InvoiceStatus, InvoiceValue, ...) from MyFatoorah's GetPaymentStatus
        # endpoint first, then find the transaction via _search_by_reference()
        # and record the payload via _record().
        payment_id = data.get('paymentId') or data.get('Id')
        company = (
            request.website.company_id
            if hasattr(request, 'website') and request.website
            else request.env.company
        )
        provider_sudo = request.env['payment.provider'].sudo().search([
            ('code', '=', 'myfatoorah'),
            ('company_id', '=', company.id),
            ('myfatoorah_token', '!=', False),
        ], limit=1) or request.env['payment.provider'].sudo().search([
            ('code', '=', 'myfatoorah'),
            ('myfatoorah_token', '!=', False),
        ], limit=1)
        if payment_id and provider_sudo:
            payment_data = provider_sudo._myfatoorah_get_payment_status(
                payment_id)
            tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference(
                'myfatoorah', payment_data)
            if not tx_sudo:
                monitored_tx_id = request.session.get(
                    PaymentStatus.MONITORED_TX_ID_KEY)
                if monitored_tx_id:
                    candidate_tx = request.env['payment.transaction'].sudo().browse(
                        monitored_tx_id).exists()
                    if candidate_tx and candidate_tx.provider_code == 'myfatoorah':
                        tx_sudo = candidate_tx
            if tx_sudo:
                PaymentStatus.monitor_transaction(tx_sudo)
                tx_sudo._record(payment_data)
            else:
                _logger.warning(
                    "No transaction found matching MyFatoorah payment data:\n%s",
                    pprint.pformat(payment_data))
        else:
            _logger.warning(
                "MyFatoorah return URL called without a paymentId, or no "
                "configured MyFatoorah provider with a token was found.")
        return request.redirect('/payment/status')

    @http.route('/payment/myfatoorah/failed', type='http', auth='public',
                website=True)
    def payment_failed(self, **kwargs):
        """ Function to render the payment failed cases"""
        return request.render(
            "myfatoorah_payment_gateway.myfatoorah_payment_gateway_failed_form")
