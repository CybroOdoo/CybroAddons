# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import logging
from pay_ccavenue import CCAvenue
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentCCAvenue(http.Controller):
    """
    Controller for handling payment-related operations with CCAvenue.
    Methods:
        avenue_return: Handle the return from CCAvenue payment gateway.
    """
    _return_url = '/payment/ccavenue/return'
    _cancel_url = '/payment/ccavenue/cancel'

    @http.route(['/payment/ccavenue/return', '/payment/ccavenue/cancel'],
                type='http', auth='public',
                methods=['POST'], csrf=False, save_session=False)
    def avenue_return(self, **post):
        """
        Handle the return from CCAvenue payment gateway.

        :param post: The POST data received from CCAvenue.
        :type post: dict

        This method processes the return data from the CCAvenue payment
        gateway, decrypts the data, and updates the payment transaction
        accordingly. After processing, it redirects to the '/payment/status'
        URL.

        :return: A redirection to the '/payment/status' URL.
        :rtype: werkzeug.wrappers.Response
        """
        if post:
            payment_provider = request.env['payment.provider'].sudo().search(
                [('code', '=', 'avenue')])
            web_url = request.env[
                'ir.config_parameter'].sudo().get_param('web.base.url')
            # Create an instance of CCAvenue
            ccavenue = CCAvenue(payment_provider.working_key,
                                payment_provider.access_code,
                                payment_provider.merchant_key,
                                web_url + '/payment/ccavenue/return',
                                web_url + '/payment/ccavenue/cancel')
            # Decrypt the data using the instance
            decrypted_data = ccavenue.decrypt(post)
            tx_sudo = request.env[
                'payment.transaction'].sudo()._get_tx_from_notification_data(
                'avenue', decrypted_data)
            tx_sudo._handle_notification_data('avenue', decrypted_data)
        return request.redirect('/payment/status')
