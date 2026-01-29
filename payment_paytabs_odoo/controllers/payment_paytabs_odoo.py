# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import logging
import pprint
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentPaytabs(http.Controller):
    """
    Controller for handling payment-related operations with Paytabs.
    Methods:
        paytabs_return: Handle the return from Paytabs payment gateway.
    """
    _return_url = '/payment/paytabs/return'

    @http.route(
        _return_url, type='http', auth='public', methods=['GET', 'POST'],
        csrf=False,
        save_session=False
    )
    def paytabs_return(self, **data):
        """
        Handle the return from PayTabs payment gateway.

        This method is used when PayTabs sends a notification with payment
        data. It retrieves the transaction data, handles the notification
        data, and redirects the user to the payment status page.

        :param post: The POST data received from PayTabs.
        :return: A redirect response to the payment status page.
        """
        _logger.info("entering _handle_feedback_data with data:\n%s",
                     pprint.pformat(data))
        request.env['payment.transaction'].sudo()._handle_feedback_data(
            'paytabs', data)
        return request.redirect('/payment/status')
