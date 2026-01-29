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
from odoo import api, fields, models, _


class TwilioSmS(models.Model):
    """Can send sms, select the receiver and template or content,
    then can send the sms"""
    _name = 'twilio.sms'
    _description = 'Twilio SmS'

    name = fields.Char(string='Name', help='Name', required=True)
    partner_id = fields.Many2one('twilio.sms.group',
                                 string='Select Receiving Group',
                                 help='Select the receiving groups',
                                 required=True)
    template_body_id = fields.Many2one('twilio.sms.template',
                                       string='Message Template',
                                       help='Select the message template')
    content = fields.Text(string='Content', help='Content', required=True)
    scheduled_date = fields.Date('Scheduled Date', help='Scheduled Date',
                                 default=fields.Date.today)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('sent', 'Sent'),
    ], string="State", default='draft', help='State of the sms')

    @api.onchange('template_body_id')
    def onchange_template_body_id(self):
        """Add the content when select the template"""
        self.content = self.template_body_id.content

    def action_confirm_sms(self):
        """Send sms when click the action button"""
        for val in self:
            val.state = 'confirm'
            if val.scheduled_date == fields.Date.today():
                self.sent_sms_message(val)

    def sent_sms_on_time(self):
        """Send sms when schedule the time"""
        vals = self.env['twilio.sms'].search([])
        for val in vals:
            if (val.state == 'confirm' and val.scheduled_date ==
                    fields.date.today()):
                self.sent_sms_message(val)

    def sent_sms_message(self, val):
        """Send SmS for all users"""
        server = self.env['twilio.account'].search([('state', '=', 'confirm')],
                                                   limit=1)
        count = len(val.partner_id.contact_ids)
        for partner in val.partner_id.contact_ids:
            try:
                client = Client(server.account_sid, server.auth_token)
                message = client.messages.create(
                    body=val.content,
                    from_=server.from_number,
                    to=partner.phone
                )
                if message.sid:
                    count = count - 1
                if not count:
                    val.state = 'sent'
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Message Sent Successfully',
                            'type': 'success',
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
