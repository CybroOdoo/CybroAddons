# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SmsGatewayConfig(models.Model):
    """
    Class to save the user credential details for the SMS gateways.
    """
    _name = 'sms.gateway.config'
    _description = 'SMS Gateway Configuration'
    _rec_name = 'gateway_name'

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
    telesign_customer = fields.Char(
        string='TeleSign Customer ID', help='Customer ID for TeleSign.')
    telesign_api_key = fields.Char(
        string='TeleSign API Key', help='API key for TeleSign')

    @api.constrains('sms_gateway_id')
    def _check_credentials(self):
        """ Check whether all the credential field have values"""
        if self.sms_gateway_id.name == 'telesign':
            if not self.telesign_customer or not self.telesign_api_key:
                raise UserError(
                    _('Provide correct credentials for Telesign'))
        if self.sms_gateway_id.name == 'vonage':
            if not self.vonage_key or not self.vonage_secret:
                raise UserError(
                    _('Provide correct credentials for Vonage'))
        if self.sms_gateway_id.name == 'twilio':
            if (not self.twilio_phone_number or not self.twilio_auth_token
                    or not self.twilio_account_sid):
                raise UserError(
                    _('Provide correct credentials for Twilio'))
