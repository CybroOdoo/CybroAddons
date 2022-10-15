# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ASWATHI C (odoo@cybrosys.com)
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
# pylint: disable=import-error
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=too-many-locals
# pylint: disable=unused-argument
# pylint: disable=inconsistent-return-statements
# pylint: disable=too-few-public-methods
# pylint: disable=bare-except
# pylint: disable=super-with-arguments

from twilio.rest import Client
from odoo import fields, models, api


class POSOrderInherit(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create_from_ui(self, orders, draft=False):
        res = super(POSOrderInherit, self).create_from_ui(orders)
        ids = []
        for line in res:
            if line['id']:
                ids.append(line['id'])
        backend_order = self.search([('id', 'in', ids)])
        if backend_order:
            for pos_order in backend_order:
                config_id = pos_order.session_id.config_id
                if config_id.customer_msg:
                    if pos_order.partner_id.phone:
                        try:
                            customer_phone = str(pos_order.partner_id.phone)
                            twilio_number = config_id.twilio_number
                            auth_token = config_id.auth_token
                            account_sid = config_id.account_sid
                            body = config_id.sms_body

                            # Download the helper library from
                            # https://www.twilio.com/docs/python/install

                            client = Client(account_sid, auth_token)
                            client.messages.create(
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
                        except:
                            pass
            return res


class POSGreetings(models.Model):
    _name = 'pos.greetings'
    _description = 'POS Greetings'

    customer_id = fields.Many2one('res.partner', string='Customer')
    order_id = fields.Many2one('pos.order', string='Order')
    auth_token = fields.Char('Token')
    twilio_number = fields.Char('Twilio Number')
    to_number = fields.Char('Customer Number')
    sms_body = fields.Char('Body', required=True)
    session_id = fields.Many2one('pos.session', string='Session')
    send_sms = fields.Boolean(string='Send SMS', default=False)


class ResConfigSettings(models.Model):
    _inherit = 'pos.config'

    customer_msg = fields.Boolean('POS Greetings',
                                  Help='Create an account if you ever create '
                                       'an account')
    auth_token = fields.Char('Auth Token',
                             Help='Copy the token from your twilio console '
                                  'window adn paste here',
                             required=True)
    account_sid = fields.Char('Account SID',
                              required=True)
    twilio_number = fields.Char('Twilio Number',
                                Help='The number provided by twilio used to '
                                     'send text messages',
                                required=True)
    sms_body = fields.Text('Body',
                           required=True)
