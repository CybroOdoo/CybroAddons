# -*- coding: utf-8 -*-
"""
This module contains the ResConfigSettings model for POS greetings integration.
"""
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """This model inherits the 'res.config.settings' model to provide
       configuration options for the POS Greetings module.Users can configure
       settings for sending SMS messages to customers using Twilio."""
    _inherit = 'res.config.settings'

    customer_msg = fields.Boolean('POS Greetings',
                                  config_parameter='pos_greetings.customer_msg',
                                  help='Create an account if you '
                                       'ever create an account')
    auth_token = fields.Char('Auth Token',
                             config_parameter='pos_greetings.auth_token',
                             help='Copy the token from your twilio console '
                                  'window and paste here', required=True)
    account_sid = fields.Char('Account SID',
                              config_parameter='pos_greetings.account_sid',
                              required=True)
    twilio_number = fields.Char('Twilio Number',
                                config_parameter='pos_greetings.twilio_number',
                                help='The number provided by '
                                     'twilio used to send '
                                     'text messages',
                                required=True)
    sms_body = fields.Char('Body', required=True,
                           config_parameter='pos_greetings.sms_body')
