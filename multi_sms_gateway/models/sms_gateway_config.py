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

""" This module helps to configure different SMS gateway. """
from odoo import fields, models


class SmsGatewayConfig(models.Model):
    """
    Class to save the user credential details for the SMS gateways.
    """
    _name = 'sms.gateway.config'
    _description = 'SMS Gateway Configuration'
    _rec_name = 'gateway_name'

    api_method = fields.Char(
        string='API Method', help='The API method that has to be used.')
    url = fields.Char(
        sring='Gateway URL', help='Gateway URL to send the message.')
    connection_ids = fields.One2many(
        'sms.connection.params', 'sms_gateway_config_id', string='Parameters',
        help='Connection parameters for the SMS gateway.')
    sms_gateway_id = fields.Many2one(
        'sms.gateway', string='Gateway', help='The SMS Gateway.')
    gateway_name = fields.Char(
        related='sms_gateway_id.name', help='Gateway Name')
    vonage_key = fields.Char(string='Key', help='The key for Vonage')
    vonage_secret = fields.Char(string='Secret', help='The secret for Vonage.')
    twilio_account_sid = fields.Char(
        string='Account SID', help='Account SID for Twilio.')
    twilio_auth_token = fields.Char(
        string='Auth Token', help='Auth token for Twilio.')
    twilio_phone_number = fields.Char(
        string='Twilio Number', help='Twilio phone number.')
    d7_username = fields.Char(string='Username', help='D7 username.')
    d7_password = fields.Char(string='Password', help=' D7 password.')
    d7_from = fields.Char(string='From', help='D7 from phone number.')
    telesign_customer = fields.Char(
        string='TeleSign Customer ID', help='Customer ID for TeleSign.')
    telesign_api_key = fields.Char(
        string='TeleSign API Key', help='API key for TeleSign')
    telnyx_number = fields.Char(string='Telnyx Number', help='Telnyx number.')
    telnyx_api_key = fields.Char(
        string='Telnyx API Key', help='API key for Telnyx.')
    messagebird_api_key = fields.Char(
        string='MessageBird API Key', help='API key for MessageBird.')
