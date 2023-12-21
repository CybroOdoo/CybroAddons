# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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


class PosGreetings(models.Model):
    """Model for creating pos greetings details"""
    _name = 'pos.greetings'
    _description = 'POS Greetings'
    _rec_name = 'order_id'

    customer_id = fields.Many2one('res.partner',
                                  help="Select customer for sending greetings",
                                  string='Customer')
    order_id = fields.Many2one('pos.order',
                               help="Pos order details of related to the "
                                    "greeting messages",
                               string='Order')
    auth_token = fields.Char(string="Token",
                             help="Authentication token for sending "
                                  "greetings messages")
    twilio_number = fields.Char('Twilio Number',
                                help="Twilio number for sending greetings "
                                     "messages")
    to_number = fields.Char('Customer Number',
                            help="Add the receiver number for sending "
                                 "greetings")
    sms_body = fields.Char('Body', required=True,
                           help="Body of the greetings message")
    session_id = fields.Many2one('pos.session', string='Session',
                                 help="Pos session id which the greetings "
                                      "messages related to")
    send_sms = fields.Boolean(string='Send SMS',
                              help="Used for identifying is the sms is send "
                                   "or not ",
                              default=False)
