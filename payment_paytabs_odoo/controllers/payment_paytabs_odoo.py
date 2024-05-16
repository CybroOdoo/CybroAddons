# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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
from odoo import http
from odoo.http import request


class PaymentPaytabs(http.Controller):
    """
    Controller for handling payment-related operations with Paytabs.
    Methods:
        paytabs_return: Handle the return from Paytabs payment gateway.
    """
    _return_url = '/payment/paytabs/return'

    @http.route(_return_url, type='http', auth='public',
                methods=['POST'], csrf=False, save_session=False)
    def paytabs_return(self, **post):

        """
        Handle the return from PayTabs payment gateway.

        This method is used when PayTabs sends a notification with payment
        data. It retrieves the transaction data, handles the notification
        data, and redirects the user to the payment status page.

        :param post: The POST data received from PayTabs.
        :return: A redirect response to the payment status page.
        """
        tx_sudo = request.env[
            'payment.transaction'].sudo()._get_tx_from_notification_data(
            'paytabs', post)
        tx_sudo._handle_notification_data('paytabs', post)
        return request.redirect('/payment/status')
