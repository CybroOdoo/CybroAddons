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
"""Configuration settings for Twilio SMS signup."""
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit the base settings to add a Twilio sender phone number."""

    _inherit = 'res.config.settings'

    twilio_from_number = fields.Char(
        help="The Twilio phone number used as the sender for outgoing "
             "SMS verification codes.",
        config_parameter='signup_with_twilio.twilio_from_number')
