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
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResCompany(TransactionCase):
    """Test the validation of the company WhatsApp number."""

    @classmethod
    def setUpClass(cls):
        """Create a company."""
        super().setUpClass()
        cls.company = cls.env['res.company'].create({
            'name': 'WhatsApp Test Company',
        })

    def test_01_valid_number(self):
        """A number of digits only, longer than 8 digits, is accepted."""
        self.company.whatsapp_number = '919876543210'
        self.assertEqual(self.company.whatsapp_number, '919876543210')

    def test_02_empty_number(self):
        """The number can be left empty."""
        self.company.whatsapp_number = False
        self.assertFalse(self.company.whatsapp_number)

    def test_03_invalid_numbers(self):
        """Letters, spaces, signs and short numbers are refused."""
        for number in ['12345678a', '12345678', '12345 6789', '+919876543210',
                       '91-98765-43210']:
            with self.subTest(number=number), \
                    self.assertRaises(ValidationError):
                self.company.whatsapp_number = number
