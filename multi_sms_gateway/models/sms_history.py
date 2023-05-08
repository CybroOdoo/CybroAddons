# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
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
