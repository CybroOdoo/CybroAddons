# -*- coding: utf-8 -*-
"""
This module contains the PosOrder model for POS greetings integration.
"""
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
#############################################################################
import logging
import re
from twilio.rest import Client
from odoo import api, models

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    """This class inherit the 'pos.order' model to add functionality for
       sending SMS messages to customers when orders are created."""
    _inherit = 'pos.order'

    @api.model
    def sync_from_ui(self, orders):
        """Create POS orders from the user interface and send SMS messages to
           customers. This method creates POS orders from the provided data and
           sends SMS messages to customers if the 'customer_msg' parameter is
           set and the customer has a valid phone number."""
        res = super().sync_from_ui(orders)

        # Get the created/updated order IDs
        pos_order_ids = res.get('pos.order', [])
        order_ids = [order['id'] for order in pos_order_ids if order.get('id')]

        if backend_order := self.search([('id', 'in', order_ids)]):
            params = self.env['ir.config_parameter'].sudo()
            customer_msg = params.get_param('pos_greetings.customer_msg')
            auth_token = params.get_param('pos_greetings.auth_token')
            account_sid = params.get_param('pos_greetings.account_sid')
            twilio_number = params.get_param('pos_greetings.twilio_number')
            sms_body = params.get_param('pos_greetings.sms_body')
            for pos_order in backend_order:
                if customer_msg and pos_order.partner_id.phone:
                    customer_phone = self._normalize_phone(
                        pos_order.partner_id.phone)
                    sms_sent = False
                    try:
                        client = Client(account_sid, auth_token)
                        client.messages.create(
                            body=sms_body,
                            from_=twilio_number,
                            to=customer_phone
                        )
                        sms_sent = True
                    except Exception as err:
                        _logger.warning(
                            "POS Greetings: Failed to send SMS to %s. "
                            "Error: %s", customer_phone, str(err))
                    # Always create the greeting record regardless of SMS result
                    self.env['pos.greetings'].create({
                        'customer_id': pos_order.partner_id.id,
                        'order_id': pos_order.id,
                        'auth_token': auth_token,
                        'twilio_number': twilio_number,
                        'to_number': customer_phone,
                        'session_id': pos_order.session_id.id,
                        'sms_body': sms_body,
                        'send_sms': sms_sent,
                    })
        return res

    @api.model
    def _normalize_phone(self, phone):
        """Normalize any phone number format to E.164 for Twilio."""
        # Separate the leading '+' from the rest before stripping
        stripped = phone.strip()
        has_plus = stripped.startswith('+')
        digits = re.sub(r'\D', '', stripped)
        if has_plus:
            # Already international format - keep as-is
            return '+' + digits
        # US/Canada 10-digit number
        if len(digits) == 10:
            return '+1' + digits
        # US 11-digit beginning with '1' (e.g. 18709310505)
        if len(digits) == 11 and digits.startswith('1'):
            return '+' + digits
        # Anything else: prepend '+'
        return '+' + digits
