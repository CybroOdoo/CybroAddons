# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class SmsHistory(models.Model):
    """
    Model to record the delivery log and audit trail of dispatched SMS messages.
    Stores gateway provider, dispatch date, recipient phone numbers, message content,
    and company details.
    """
    _name = 'sms.history'
    _description = 'SMS Delivery History'
    _rec_name = 'sms_mobile'
    _order = 'sms_date desc, id desc'

    sms_gateway_id = fields.Many2one(
        'sms.gateway',
        string='Gateway',
        readonly=True,
        help='The SMS gateway provider used to send the message.'
    )
    sms_date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        readonly=True,
        help='Date and timestamp when the SMS was dispatched.'
    )
    sms_mobile = fields.Char(
        string='Mobile Number',
        readonly=True,
        help='Destination phone number(s) to which the SMS was sent.'
    )
    sms_text = fields.Text(
        string='SMS Text',
        readonly=True,
        help='Content of the SMS message sent to the recipient(s).'
    )
    company_id = fields.Many2one(
        'res.company',
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
        help='Company from which the SMS was dispatched.'
    )
