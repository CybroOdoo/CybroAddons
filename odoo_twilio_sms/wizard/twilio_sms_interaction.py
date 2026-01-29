# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from twilio.rest import Client
from odoo import api, fields, models, _


class TwilioSmsInteraction(models.TransientModel):
    """ Class to handle all the functions required in send sms """
    _name = 'twilio.sms.interaction'
    _description = 'Twilio SmS Interaction'

    partner_id = fields.Many2one('res.partner', string='Recipient',
                                 help='Receiving User')
    receiving_number = fields.Char(string='Receiving Number',
                                   help='Receiving Number',
                                   required=True, readonly=False,
                                   related='partner_id.phone')
    template_id = fields.Many2one('twilio.sms.template',
                                  string='Select Template',
                                  help='Message Template')
    text_message = fields.Text(string='Message', help='Message Content',
                               required=True)

    @api.onchange('template_id')
    def onchange_template_id(self):
        """Add content when select the template"""
        if self.template_id:
            self.text_message = self.template_id.content

    def action_confirm_sms(self):
        """Send sms to the corresponding user by using the twilio connection"""
        server = self.env['twilio.account'].search([('state', '=', 'confirm')],
                                                   limit=1)
        try:
            client = Client(server.account_sid, server.auth_token)
            message = client.messages.create(
                body=self.text_message,
                from_=server.from_number,
                to=self.receiving_number
            )
            if message.sid:
                message_data = _("Message Sent!")
                type_data = 'success'
            else:
                message_data = _("Message Not Sent!")
                type_data = 'warning'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message_data,
                    'type': type_data,
                    'sticky': True,
                }
            }
        except:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Message Not Sent!"),
                    'type': 'warning',
                    'sticky': True,
                }
            }
            pass
