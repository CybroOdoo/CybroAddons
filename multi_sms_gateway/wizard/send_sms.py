# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
import vonage
from vonage_sms import SmsMessage
from telesign.messaging import MessagingClient
from twilio.rest import Client
from odoo import fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


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
            try:
                client = vonage.Vonage(vonage.Auth(
                    api_key=self.sms_id.vonage_key,
                    api_secret=self.sms_id.vonage_secret
                ))
                for number in self.sms_to.split(','):
                    if number:
                        response = client.sms.send(SmsMessage(
                            to=number,
                            from_='Vonage APIs',
                            text=self.text
                        ))
                        if response.messages[0].status == "0":
                            _logger.info("Message sent successfully.")
                        else:
                            _logger.info(
                                f"Message failed with error: {response.messages[0].error_text}")
                            raise UserError(
                                f"Message failed with error: {response.messages[0].error_text}")
            except Exception as e:
                raise UserError('Error ' + str(e))
        elif self.sms_id.gateway_name == 'twilio':
            client = Client(self.sms_id.twilio_account_sid,
                            self.sms_id.twilio_auth_token)
            for number in self.sms_to.split(','):
                if number:
                    try:
                        client.messages.create(
                            body=self.text,
                            from_=int(self.sms_id.twilio_phone_number),
                            to=number
                        )
                    except Exception as e:
                        raise UserError('Provide correct credentials ' + str(e))
        elif self.sms_id.gateway_name == 'telesign':
            for number in self.sms_to.split(','):
                if number:
                    try:
                        messaging = MessagingClient(
                            self.sms_id.telesign_customer,
                            self.sms_id.telesign_api_key)
                        messaging.message(number, self.text, 'ARN')
                    except Exception as e:
                        raise UserError('Provide correct credentials ' + str(e))
        self.env['sms.history'].sudo().create({
            'sms_gateway_id': self.sms_id.sms_gateway_id.id,
            'sms_mobile': self.sms_to,
            'sms_text': self.text
        })
        message_body = (
                f"Message: {self.text}"
        )
        partner = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        partner.message_post(
            body=message_body,
            message_type="comment",
            subtype_xmlid="mail.mt_comment"
        )
