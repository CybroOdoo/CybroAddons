# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:ISMAIL C A(odoo@cybrosys.com)
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

###############################################################################
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestResCompany(TransactionCase):

    def setUp(self):
        super(TestResCompany, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'WhatsApp Test Company',
        })

    def test_check_whatsapp_number_valid(self):
        """Test valid WhatsApp number."""
        self.company.whatsapp_number = '123456789'
        self.company._check_whatsapp_number()

    def test_check_whatsapp_number_invalid_not_numeric(self):
        """Test invalid WhatsApp number (not numeric)."""
        with self.assertRaises(UserError):
            self.company.write({'whatsapp_number': '12345678a'})
            self.company._check_whatsapp_number()

    def test_check_whatsapp_number_invalid_short(self):
        """Test invalid WhatsApp number (too short)."""
        with self.assertRaises(UserError):
            self.company.write({'whatsapp_number': '12345678'})
            self.company._check_whatsapp_number()

    def test_check_whatsapp_number_invalid_space(self):
        """Test invalid WhatsApp number (contains space)."""
        with self.assertRaises(UserError):
            self.company.write({'whatsapp_number': '12345 6789'})
            self.company._check_whatsapp_number()
