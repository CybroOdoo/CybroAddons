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
import logging
import requests

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class NetworkInternational(http.Controller):
    """Network International Payment Controller."""

    _return_url = '/payment/network_international/return'

    @http.route(
        _return_url,
        type='http',
        auth='public',
        csrf=False,
        save_session=False
    )
    def ni_return(self, **post):
        """Handle return from Network International."""

        ref = post.get('ref')
        if not ref:
            raise ValidationError("Missing payment reference from Network International.")

        payment_ni = request.env['payment.provider'].sudo().search(
            [('code', '=', 'network_international')],
            limit=1
        )

        if not payment_ni:
            raise ValidationError("Network International provider not found.")

        outlet_reference = payment_ni.outlet_reference
        api_endpoint = payment_ni.api_endpoint

        # Generate fresh token
        token_response = payment_ni._get_authentication_token(
            f"{api_endpoint}/identity/auth/access-token"
        )

        auth_token = token_response.get('access_token')
        if not auth_token:
            raise ValidationError(
                f"Unable to get Network International access token: {token_response}"
            )

        url = (
            f"{api_endpoint}/transactions/outlets/"
            f"{outlet_reference}/orders/{ref}"
        )

        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/vnd.ni-payment.v2+json",
        }

        _logger.info("NI Return URL: %s", url)

        try:
            resp = requests.get(url, headers=headers, timeout=60)

            _logger.info("NI Status Code: %s", resp.status_code)
            _logger.info("NI Response Text: %s", resp.text)

            resp.raise_for_status()

            try:
                response = resp.json()
            except ValueError:
                raise ValidationError(
                    f"Network International returned invalid JSON: {resp.text}"
                )

            tx_sudo = request.env[
                'payment.transaction'
            ].sudo()._get_tx_from_notification_data(
                'network_international',
                response
            )

            if not tx_sudo:
                raise ValidationError(
                    f"No transaction found for response: {response}"
                )

            tx_sudo._handle_notification_data(
                'network_international',
                response
            )

        except Exception as error:
            _logger.exception(
                "Network International return processing failed"
            )
            raise ValidationError(str(error))

        return request.redirect('/payment/status')