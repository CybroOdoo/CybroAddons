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
from odoo import fields, models


class SmsGateway(models.Model):
    """
    Model representing supported SMS Gateway service providers.
    Stores provider definitions such as Vonage, Twilio, and TeleSign.
    """
    _name = 'sms.gateway'
    _description = 'SMS Gateway Provider'

    name = fields.Char(
        string='Provider Name',
        required=True,
        help='Unique identifier name of the SMS gateway provider (e.g., vonage, twilio, telesign).'
    )
