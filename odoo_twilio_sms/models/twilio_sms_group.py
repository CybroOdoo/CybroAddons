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


class TwilioSmsGroup(models.Model):
    """Group of contacts that receive the same SMS"""
    _name = 'twilio.sms.group'
    _description = 'Twilio SMS Group'

    name = fields.Char(help='Name of the group', required=True)
    contact_ids = fields.Many2many('res.partner',
                                   'twilio_sms_group_partner_rel',
                                   'group_id', 'partner_id',
                                   string='Members',
                                   help='Contacts in the group')
