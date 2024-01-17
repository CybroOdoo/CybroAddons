# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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


class POSGreetings(models.Model):
    """Model representing POS Greetings."""
    _name = 'pos.greetings'
    _description = 'POS Greetings'
    _rec_name = 'order_id'

    partner_id = fields.Many2one('res.partner', string='Customer',
                                 help='Select the customer for whom the SMS '
                                      'will be sent.')
    order_id = fields.Many2one('pos.order', string='Order',
                               help='Select the order associated with the SMS')
    auth_token = fields.Char(string='Token',
                             help='Enter the authentication token for the SMS '
                                  'service provider.')
    twilio_number = fields.Char(string='Twilio Number',
                                help='Enter the Twilio phone number used to'
                                     ' send the SMS.')
    to_number = fields.Char(string='Customer Number',
                            help='Enter the recipients phone number to send '
                                 'the SMS to.')
    sms_body = fields.Char(string='Body',
                           help='Enter the content or message of the SMS.')
    session_id = fields.Many2one('pos.session', string='Session',
                                 help='Select the session associated with '
                                      'the SMS.')
    send_sms = fields.Boolean(string='Send SMS',help='Check this box to send '
                                            'the SMS when saving the record.')
