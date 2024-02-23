# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
################################################################################
from __future__ import print_function
import clicksend_client
import logging
from ast import literal_eval
from clicksend_client import SmsMessage
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SendSms(models.TransientModel):
    """This Transient model will read all the user inputs and sends sms"""
    _name = 'send.sms'
    _description = "Send SMS for a Partner ,Group or Anyone"

    number = fields.Char(string='Number', related='partner_id.phone',
                         readonly=False,
                         store=True, help="Phone number of the Partner")
    name = fields.Char(string="Name", help="Name of the Receiver")
    partner_id = fields.Many2one('res.partner', string="Partner",
                                 help="Receiver name")
    message = fields.Text(string='Message', help="Content of the SMS Message")
    group_id = fields.Many2one('sms.group', string='Group',
                               help="Choose a group to send the sms")
    partner_ids = fields.Many2many('res.partner', string="Partners",
                                   help="The partners to send SMS",
                                   related='group_id.partner_ids')

    def action_send_sms(self):
        """   Send SMS using ClickSend API.
        This method retrieves ClickSend credentials from Odoo configuration
        parameters, constructs SMS messages based on the recipient information,
        and sends the SMS using the ClickSend API. It logs the SMS history
        with details like  recipient name, number, message, and delivery
        status."""
        username = self.env['ir.config_parameter'].sudo().get_param(
            'clicksend_sms_odoo.username')
        password = self.env['ir.config_parameter'].sudo().get_param(
            'clicksend_sms_odoo.api_key')
        if not username or not password:
            raise UserError(_("Please configure your ClickSend credentials"))
        configuration = clicksend_client.Configuration()
        configuration.username = username
        configuration.password = password
        api_instance = clicksend_client.SMSApi(
            clicksend_client.ApiClient(configuration))
        num_list = []
        name_list = []
        number = False
        if self.partner_id:
            number = self.partner_id.phone
        elif self.name and self.number:
            number = self.number
        elif self.group_id:
            partner_ids = self.group_id.partner_ids
            num_list = partner_ids.mapped('phone')
            name_list = partner_ids.mapped('name')
        if number:
            sms_message = SmsMessage(
                source="php",
                body=self.message,
                to=number,
                schedule=1436874701
            )
        else:
            sms_messages = [SmsMessage(
                source="php",
                body=self.message,
                to=num,
                schedule=1436874701
            ) for num in num_list]
        try:
            if number:
                api_response = api_instance.sms_send_post(
                    clicksend_client.SmsMessageCollection(
                        messages=[sms_message]))
            else:
                api_response = api_instance.sms_send_post(
                    clicksend_client.SmsMessageCollection(
                        messages=sms_messages))
            response = api_response.replace("\'", "\"")
            response = literal_eval(response)
            if response.get('response_code') == 'SUCCESS':
                state = "sent"
            else:
                state = "canceled"
            name = self.name if self.name else (
                self.partner_id.name if self.partner_id else "")
            if number:
                self.env['sms.history'].create({
                    'name': name,
                    'number': number,
                    'state': state,
                    'message': self.message
                })
            else:
                for num, name in zip(num_list, name_list):
                    self.env['sms.history'].create({
                        'name': name,
                        'number': num,
                        'state': state,
                        'message': self.message
                    })
        except Exception as e:
            _logger.warning(
                "Exception when calling SMSApi->sms_send_post: %s\n" % e)
            raise ValidationError(
                _("An error occurred while sending SMS. Please check your "
                  "Credentials and try again."))
