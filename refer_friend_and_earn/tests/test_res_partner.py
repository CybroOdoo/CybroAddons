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
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestResPartner(TransactionCase):
    """Test suite for res.partner model referral fields."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Referral Partner',
            'email': 'referral_test@example.com',
        })

    def test_default_values(self):
        """Test default points, sign_up, and referral_code values on partner."""
        self.assertEqual(self.partner.points, 0)
        self.assertEqual(self.partner.sign_up, 0)
        self.assertFalse(self.partner.referral_code)

    def test_referral_fields(self):
        """Test assigning and updating referral fields on res.partner."""
        self.partner.write({
            'referral_code': 'REFCODE123',
            'points': 45,
            'sign_up': 3,
        })
        self.assertEqual(self.partner.referral_code, 'REFCODE123')
        self.assertEqual(self.partner.points, 45)
        self.assertEqual(self.partner.sign_up, 3)
