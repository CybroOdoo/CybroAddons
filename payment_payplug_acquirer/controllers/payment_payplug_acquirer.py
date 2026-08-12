# -*- coding: utf-8 -*-
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
#############################################################################
import payplug
from odoo import http
from odoo.http import request


class PaymentPayPlug(http.Controller):
    """
    Controller for handling payment-related operations with payplug.
    Methods:
        payplug_return: Handle the return from payplug payment gateway.
    """
    _return_url = '/payment/payplug/return'

    @http.route(_return_url, type='http', auth='public', csrf=False,
                save_session=False)
    def payplug_return(self, **post):
        """
        Handle the return from PayPlug payment gateway.

        This method is used when PayPlug sends a notification with payment
        data. It retrieves the transaction data and redirects the user to
        the payment status page.

        :param post: The POST data received from PayPlug.
        :return: A redirect response to the payment status page.
        """
        payment = request.env['payment.transaction'].sudo().browse(
            int(post.get('transaction')))
        payplug.set_secret_key(payment.provider_id.payplug_secret_key)
        payment_payplug = payplug.Payment.retrieve(
            str(payment.provider_reference))
        tx_sudo = request.env[
            'payment.transaction'].sudo()._get_tx_from_notification_data(
            'payplug', payment_payplug)
        tx_sudo._handle_notification_data('payplug', payment_payplug)
        return request.redirect('/payment/status')
