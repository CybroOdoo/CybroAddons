# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ansil pv (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import logging
import pprint
from odoo import http
from odoo.http import request
from wallee import Configuration
from wallee.api import TransactionServiceApi
_logger = logging.getLogger(__name__)


class PaymentWalleeController(http.Controller):
    """
        PaymentWalleeController class provides the functionality of redirecting
        of Wallee payment page to Odoo payment status page and pass status to
        value to transaction functions
        Methods:
            webhook_listener(self):
                for fetching payment status from Wallee webhook service and
                redirecting to Odoo payment status page and pass status
    """
    @http.route('/webhook', type='http', auth='public',
                methods=['GET', 'POST'], csrf=False, save_session=False)
    def webhook_listener(self):
        """
           For pass records transaction model and redirect to status page
        """
        value = {}
        data = request.env['payment.transaction'].sudo().search(
            [('provider_id.code', '=', 'wallee')])
        for transaction in data:
            if transaction.provider_reference:
                config = Configuration(
                    user_id=transaction.provider_id.wallee_user_id,
                    api_secret=transaction.provider_id.wallee_user_secret_key,
                    # set a custom request timeout if needed.
                    # (If not set, then the default value is: 25 seconds)
                    request_timeout=30
                )
                transaction_service = TransactionServiceApi(
                    configuration=config)
                transaction_read = transaction_service.read(
                    space_id=transaction.provider_id.wallee_user_space_id,
                    id=int(transaction.provider_reference))
                value["state"] = transaction_read.state.name
                value["reference"] = transaction.reference
                break
        _logger.info("Received Wallee return data:\n%s",
                     pprint.pformat(value))
        tx_sudo = (request.env['payment.transaction'].sudo().
                   _get_tx_from_notification_data('wallee', value))
        tx_sudo._handle_notification_data('wallee', value)
        return request.redirect('/payment/status')
