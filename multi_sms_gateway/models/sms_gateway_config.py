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
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SmsGatewayConfig(models.Model):
    """
    Model to store and manage authentication credentials and settings for SMS gateways.
    Maintains API configuration for Vonage, Twilio, and TeleSign.
    """
    _name = 'sms.gateway.config'
    _description = 'SMS Gateway Configuration'
    _rec_name = 'gateway_name'

    sms_gateway_id = fields.Many2one(
        'sms.gateway',
        string='Gateway',
        required=True,
        help='Select the SMS gateway provider (Vonage, Twilio, or TeleSign).'
    )
    gateway_name = fields.Char(
        related='sms_gateway_id.name',
        string='Gateway Name',
        help='Technical identifier name of the selected SMS gateway provider.'
    )
    gateway_provider = fields.Char(
        compute='_compute_gateway_provider',
        store=True,
        help='Normalized lowercase identifier for the gateway provider.'
    )
    vonage_key = fields.Char(
        string='Vonage API Key',
        help='API Key obtained from the Vonage developer dashboard.'
    )
    vonage_secret = fields.Char(
        string='API Secret',
        help='API Secret obtained from the Vonage developer dashboard.'
    )
    twilio_account_sid = fields.Char(
        string='Account SID',
        help='Account SID found on your Twilio project console dashboard.'
    )
    twilio_auth_token = fields.Char(
        string='Auth Token',
        help='Authentication token corresponding to your Twilio Account SID.'
    )
    twilio_phone_number = fields.Char(
        help='Sender phone number registered in Twilio in E.164 format (e.g., +17372508034).'
    )
    telesign_customer = fields.Char(
        string='Customer ID',
        help='Customer ID (UUID) provided by your TeleSign account dashboard.'
    )
    telesign_api_key = fields.Char(
        string='TeleSign API Key',
        help='REST API Key generated in your TeleSign account.'
    )

    @api.depends('sms_gateway_id.name')
    def _compute_gateway_provider(self):
        for record in self:
            record.gateway_provider = (
                record.sms_gateway_id.name or ''
            ).strip().lower()

    @api.constrains(
        'sms_gateway_id',
        'vonage_key', 'vonage_secret',
        'twilio_account_sid', 'twilio_auth_token', 'twilio_phone_number',
        'telesign_customer', 'telesign_api_key'
    )
    def _check_credentials(self):
        """
        Validate that required credential fields are populated for the selected gateway.

        Raises:
            ValidationError: If any required credential field is empty for the active gateway.
        """
        for record in self:
            gateway = record.gateway_provider or (record.sms_gateway_id.name or '').strip().lower()
            if gateway == 'telesign':
                if not record.telesign_customer or not record.telesign_api_key:
                    raise ValidationError(
                        self.env._('Please provide valid credentials for TeleSign.')
                    )
            elif gateway == 'vonage':
                if not record.vonage_key or not record.vonage_secret:
                    raise ValidationError(
                        self.env._('Please provide valid credentials for Vonage.')
                    )
            elif gateway == 'twilio':
                if (not record.twilio_phone_number or not record.twilio_auth_token
                        or not record.twilio_account_sid):
                    raise ValidationError(
                        self.env._('Please provide valid credentials for Twilio.')
                    )
