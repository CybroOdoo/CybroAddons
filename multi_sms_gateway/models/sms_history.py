# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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

""" This module helps to see the history of all SMS send. """
from odoo import fields, models


class SmsHistory(models.Model):
    """
    This model stores the details of all the SMS messages that have been
    sent, including the gateway name, date of sending, mobile phone number,
    and SMS text.
    """
    _name = 'sms.history'
    _description = 'SMS History'
    _rec_name = 'sms_mobile'

    sms_gateway_id = fields.Many2one('sms.gateway', string='Gateway',
                                     help='The SMS Gateway.')
    sms_date = fields.Datetime(string='Date', default=fields.Date().today(),
                               help='Date of sending message(current day).')
    sms_mobile = fields.Char(
        string='Mobile Number', help='Phone Number to send SMS.')
    sms_text = fields.Text(string='SMS Text', help='The message to be sent.')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company, help='Active company.')
