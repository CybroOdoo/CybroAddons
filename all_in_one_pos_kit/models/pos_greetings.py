# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)

TWILIO_URL = "https://api.twilio.com/2010-04-01/Accounts/%s/Messages.json"


class PosGreetings(models.Model):
    """Greeting message (SMS) sent to the customer of a paid POS order"""
    _name = 'pos.greetings'
    _description = 'POS Greetings'
    _rec_name = 'order_id'

    customer_id = fields.Many2one('res.partner',
                                  help="Customer who receives the greeting")
    order_id = fields.Many2one('pos.order',
                               help="POS order related to the greeting message")
    twilio_number = fields.Char(
                                help="Twilio number used to send the greeting")
    to_number = fields.Char(string='Customer Number',
                            help="Phone number that receives the greeting")
    sms_body = fields.Char(string='Body', required=True,
                           help="Text of the greeting message")
    session_id = fields.Many2one('pos.session',
                                 help="POS session of the related order")
    send_sms = fields.Boolean(string='Send SMS', default=False,
                              help="Set when the message was sent to Twilio")

    def action_send_greeting(self):
        """Send the greeting messages through the Twilio REST API.
        Credentials are read from the system parameters, so the token is
        never stored on the greeting record. A failure is logged and does
        not stop the POS order from being saved."""
        params = self.env['ir.config_parameter'].sudo()
        account_sid = params.get_param('all_in_one_pos_kit.account_sid')
        auth_token = params.get_param('all_in_one_pos_kit.twilio_auth_token')
        for greeting in self.filtered(lambda g: not g.send_sms):
            if not (account_sid and auth_token and greeting.twilio_number
                    and greeting.to_number):
                continue
            try:
                response = requests.post(
                    TWILIO_URL % account_sid,
                    data={'From': greeting.twilio_number,
                          'To': greeting.to_number,
                          'Body': greeting.sms_body},
                    auth=(account_sid, auth_token),
                    timeout=10)
                response.raise_for_status()
                greeting.send_sms = True
            except requests.RequestException as error:
                _logger.warning("POS greeting %s was not sent: %s",
                                greeting.id, error)
        return True
