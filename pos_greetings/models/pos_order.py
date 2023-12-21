# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
from twilio.rest import Client
from odoo import api, models


class PosOrder(models.Model):
    """This class inherit the 'pos.order' model to add functionality for
       sending SMS messages to customers when orders are created."""
    _inherit = 'pos.order'

    @api.model
    def create_from_ui(self, orders, draft=False):
        """Create POS orders from the user interface and send SMS messages to
           customers.This method creates POS orders from the provided data and
           sends SMS messages to customers if the 'customer_msg' parameter is
           set and the customer has a valid phone number."""
        res = super(PosOrder, self).create_from_ui(orders)
        id = [line['id'] for line in res if line['id']]
        if backend_order := self.search([('id', 'in', id)]):
            for pos_order in backend_order:
                params = self.env['ir.config_parameter'].sudo()
                customer_msg = params.get_param('pos_greetings.customer_msg')
                auth_token = params.get_param('pos_greetings.auth_token')
                account_sid = params.get_param('pos_greetings.account_sid')
                twilio_number = params.get_param('pos_greetings.twilio_number')
                sms_body = params.get_param('pos_greetings.sms_body')
                if customer_msg and pos_order.partner_id.phone:
                    try:
                        customer_phone = str(pos_order.partner_id.phone)
# Download the helper library from https://www.twilio.com/docs/python/install
                        client = Client(account_sid, auth_token)
                        message = client.messages.create(
                            body=sms_body,
                            from_=twilio_number,
                            to=customer_phone
                        )
                        self.env['pos.greetings'].create({
                            'customer_id': pos_order.partner_id.id,
                            'order_id': pos_order.id,
                            'auth_token': auth_token,
                            'twilio_number': twilio_number,
                            'to_number': customer_phone,
                            'session_id': pos_order.session_id.id,
                            'sms_body': sms_body,
                            'send_sms': True,
                        })
                    except Exception:
                        pass
            return res
