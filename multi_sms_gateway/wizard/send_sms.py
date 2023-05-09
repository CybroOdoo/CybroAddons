# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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

""" This module helps to add the sms details in the wizard and send SMS. """
import messagebird
import requests
import telnyx
import vonage
from telesign.messaging import MessagingClient
from twilio.rest import Client

from odoo import fields, models
from odoo.exceptions import UserError


class SendSms(models.TransientModel):
    """
    Class for the wizard to send SMS.
    Methods:
        action_send_sms():
            Button action to send SMS.
    """
    _name = 'send.sms'
    _description = 'Wizard to send SMS'

    sms_id = fields.Many2one('sms.gateway.config', string='Connection ID',
                             help='Gateway record with credentials')
    sms_to = fields.Char(string='Send To',
                         help='Enter the number to send the SMS')
    text = fields.Text(string='Text', required=True,
                       help='Enter the text for the SMS')

    def action_send_sms(self):
        """
        Function to send SMS using different SMS gateway
        """
        if self.sms_id.gateway_name == 'vonage':
            client = vonage.Client(key=self.sms_id.vonage_key,
                                   secret=self.sms_id.vonage_secret)
            vonage.Sms(client)
            for number in self.sms_to.split(','):
                if number:
                    client.sms.send_message(
                        {
                            "from": 'Vonage APIs',
                            "to": number,
                            "text": self.text
                        }
                    )
        elif self.sms_id.gateway_name == 'twilio':
            client = Client(self.sms_id.twilio_account_sid,
                            self.sms_id.twilio_auth_token)
            for number in self.sms_to.split(','):
                if number:
                    client.messages.create(
                        body=self.text,
                        from_=self.sms_id.twilio_phone_number,
                        to=number
                    )
        elif self.sms_id.gateway_name == 'telesign':
            for number in self.sms_to.split(','):
                if number:
                    messaging = MessagingClient(
                        self.sms_id.telesign_customer,
                        self.sms_id.telesign_api_key)
                    messaging.message(number, self.text, 'ARN')
        elif self.sms_id.gateway_name == 'd7':
            for number in self.sms_to.split(','):
                if number:
                    querystring = {
                        "username": self.sms_id.d7_username,
                        "password": self.sms_id.d7_password,
                        "from": self.sms_id.d7_from,
                        "content": """This%20is%20a%20test%20message%20to%20
                        verify%20the%20DLR%20callback""",
                        "dlr-method": "POST",
                        "dlr-url": "https://4ba60af1.ngrok.io/receive",
                        "dlr": "yes",
                        "dlr-level": "3",
                        "to": number
                    }
                    requests.request(
                        'GET', 'https://http-api.d7networks.com/send',
                        headers={'cache-control': 'no-cache'},
                        params=querystring)
        elif self.sms_id.gateway_name == 'messagebird':
            client = messagebird.Client(self.sms_id.messagebird_api_key)
            for number in self.sms_to.split(','):
                if number:
                    try:
                        client.message_create(
                            'MessageBird', number, self.text,
                            {'reference': 'Foobar'}
                        )
                    except messagebird.client.ErrorException:
                        raise UserError('Invalid parameter!')
        elif self.sms_id.gateway_name == 'telnyx':
            telnyx.api_key = self.sms_id.telnyx_api_key
            for number in self.sms_to.split(','):
                if number:
                    try:
                        telnyx.Message.create(
                            from_=self.sms_id.telnyx_number,
                            to=number,
                            text=self.text
                        )
                    except telnyx.error.InvalidRequestError:
                        raise UserError('Missing required parameter!')
        self.env['sms.history'].sudo().create({
            'sms_gateway_id': self.sms_id.sms_gateway_id.id,
            'sms_mobile': self.sms_to,
            'sms_text': self.text
        })
