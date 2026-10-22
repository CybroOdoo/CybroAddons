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
from odoo.tests.common import TransactionCase


class TwilioCommon(TransactionCase):
    """Common records for the Twilio SMS tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account = cls.env['twilio.account'].create({
            'name': 'Test Account',
            'account_sid': 'AC123',
            'auth_token': 'TOKEN',
            'from_number': '+15550000000',
            'to_number': '+15551111111',
        })
        cls.template = cls.env['twilio.sms.template'].create({
            'name': 'Greeting',
            'content': 'Hello from Odoo',
        })
        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Partner One',
            'phone': '+15552222222',
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Partner Two',
            'phone': '+15553333333',
        })
        cls.group = cls.env['twilio.sms.group'].create({
            'name': 'Customers',
            'contact_ids': [(6, 0, (cls.partner_1 | cls.partner_2).ids)],
        })
