# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: YADHU K (odoo@cybrosys.com)
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
from odoo import fields, models, api
from twilio.rest import Client


class POSOrderInherit(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create_from_ui(self, orders, draft=False):
        res = super(POSOrderInherit, self).create_from_ui(orders)
        id = [line['id'] for line in res if line['id']]
        if backend_order := self.search([('id', 'in', id)]):
            for pos_order in backend_order:
                params = self.env['ir.config_parameter'].sudo()
                customer_msg = params.get_param('pos.customer_msg')
                auth_token = params.get_param('pos.auth_token')
                account_sid = params.get_param('pos.account_sid')
                twilio_number = params.get_param('pos.twilio_number')
                sms_body = params.get_param('pos.sms_body')
                if customer_msg and pos_order.partner_id.phone:
                    try:
                        customer_phone = str(pos_order.partner_id.phone)
                        twilio_number = twilio_number
                        auth_token = auth_token
                        account_sid = account_sid
                        body = sms_body

                        # Download the helper library from https://www.twilio.com/docs/python/install

                        client = Client(account_sid, auth_token)
                        message = client.messages.create(
                            body=body,
                            from_=twilio_number,
                            to=customer_phone
                        )
                        pos_greeting_obj = self.env['pos.greetings']
                        pos_greeting_obj.create({
                            'customer_id': pos_order.partner_id.id,
                            'order_id': pos_order.id,
                            'auth_token': auth_token,
                            'twilio_number': twilio_number,
                            'to_number': customer_phone,
                            'session_id': pos_order.session_id.id,
                            'sms_body': body,
                            'send_sms': True,
                        })
                    except Exception:
                        pass
            return res


class POSGreetings(models.Model):
    _name = 'pos.greetings'
    _description = 'POS Greetings'
    _rec_name = 'order_id'

    customer_id = fields.Many2one('res.partner', string='Customer')
    order_id = fields.Many2one('pos.order', string='Order')
    auth_token = fields.Char('Token')
    twilio_number = fields.Char('Twilio Number')
    to_number = fields.Char('Customer Number')
    sms_body = fields.Char('Body', required=True)
    session_id = fields.Many2one('pos.session', string='Session')
    send_sms = fields.Boolean(string='Send SMS', default=False)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    customer_msg = fields.Boolean('POS Greetings', Help='Create an account if '
                                                        'you ever create an '
                                                        'account')
    auth_token = fields.Char('Auth Token', Help='Copy the token from your '
                                                'twilio console window adn '
                                                'paste here', required=True)
    account_sid = fields.Char('Account SID', required=True)
    twilio_number = fields.Char('Twilio Number', Help='The number provided by '
                                                      'twilio used to send '
                                                      'text messeges',
                                required=True)
    sms_body = fields.Text('Body', required=True)

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'pos.customer_msg', self.customer_msg)
        self.env['ir.config_parameter'].set_param(
            'pos.auth_token', self.auth_token)
        self.env['ir.config_parameter'].set_param(
            'pos.account_sid', self.account_sid)
        self.env['ir.config_parameter'].set_param(
            'pos.twilio_number', self.twilio_number)
        self.env['ir.config_parameter'].set_param(
            'pos.sms_body', self.sms_body)
        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        customer_msg = params.get_param('pos.customer_msg')
        auth_token = params.get_param('pos.auth_token')
        account_sid = params.get_param('pos.account_sid')
        twilio_number = params.get_param('pos.twilio_number')
        sms_body = params.get_param('pos.sms_body')
        res.update(
            customer_msg=customer_msg,
            auth_token=auth_token,
            account_sid=account_sid,
            twilio_number=twilio_number,
            sms_body=sms_body,
        )
        return res
