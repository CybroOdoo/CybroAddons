# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Busthana Shirin (odoo@cybrosys.com)
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
###############################################################################
from twilio.rest import Client
from odoo import fields, models, _


class TwilioAccount(models.Model):
    """Create twilio account to set the details of twilio account,
    can set the number and auth token"""
    _name = 'twilio.account'
    _description = 'Twilio Account'

    name = fields.Char(string='Name', required=True, help='Name')
    account_sid = fields.Char(string='Account SID', required=True,
                              help='Account SID')
    auth_token = fields.Char(string='Auth Token', required=True,
                             help='Auth Token')
    from_number = fields.Char(string='From Number', required=True,
                              help='Twilio account number')
    to_number = fields.Char(string='To Number', required=True,
                            help='Receiving number for testing')
    body = fields.Text(string='Body', required=True,
                       help='Body for test message',
                       default='This Message is To Test The Connection')
    state = fields.Selection(selection=[
        ('new', 'New'),
        ('confirm', 'Connected'),
    ], string='State', required=True, default='new',
        help='The state to show the connection is successful')

    def action_test_connection(self):
        """Send test sms and set the connection"""
        try:
            client = Client(self.account_sid, self.auth_token)
            message = client.messages.create(
                body=self.body,
                from_=self.from_number,
                to=self.to_number)
            if message.sid:
                self.state = 'confirm'
                message_data = _("Connection Successful!")
                message_type = 'success'
            else:
                message_data = _("Connection Not Successful!")
                message_type = 'warning'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message_data,
                    'type': message_type,
                    'sticky': True,
                }
            }
        except:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Connection Not Successful!"),
                    'type': 'warning',
                    'sticky': True,
                }
            }
            pass
