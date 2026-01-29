# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited Configuration Settings"""
    _inherit = "res.config.settings"

    customer_msg = fields.Boolean(string='POS Greetings',
                                  config_parameter='pos.customer_msg',
                                  help='Create an account if you ever create an'
                                       'account')
    auth_token = fields.Char(string='Auth Token',
                             config_parameter='pos.auth_token',
                             help='Copy the token from your twilio console '
                                  'window adn paste here')
    account_sid = fields.Char(string='Account SID',
                              config_parameter='pos.account_sid',
                              help='Enter the Account SID provided by Twilio '
                                   'for authentication.')
    twilio_number = fields.Char(string='Twilio Number',
                                config_parameter='pos.twilio_number',
                                help='Enter the Twilio phone number used to '
                                     'send the SMS.')
    sms_body = fields.Text(string='Body',
                           help='Enter the content or message of the SMS to be'
                                'sent.')

    def set_values(self):
        """Override method to set configuration values.
            :return: Result of the super method"""
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'pos.sms_body', self.sms_body)
        return res

    def get_values(self):
        """Override method to get configuration values.
           :return: Dictionary of configuration values"""
        res = super(ResConfigSettings, self).get_values()
        res.update(sms_body=self.env['ir.config_parameter'].sudo().get_param(
            'pos.sms_body'))
        return res
