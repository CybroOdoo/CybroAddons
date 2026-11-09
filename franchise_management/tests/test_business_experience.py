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
"""Test cases for Business Experience model."""
from datetime import date
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBusinessExperience(TransactionCase):
    """Test suite for business.experience model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agreement = cls.env['franchise.agreement'].create({
            'agreement_type': 'Monthly',
            'agreement_body': '<p>Body</p>',
        })
        cls.dealer = cls.env['franchise.dealer'].create({
            'dealer_name': 'Test Dealer',
            'dealer_mail': 'dealer_exp@test.com',
            'monthly_target_amount': 5000.0,
            'contract_type_id': cls.agreement.id,
        })

    def test_business_experience_creation(self):
        """Test creating business experience linked to a franchise dealer."""
        experience = self.env['business.experience'].create({
            'experience_name': 'Retail Sales Management',
            'from_date': date(2020, 1, 1),
            'to_date': date(2023, 1, 1),
            'experience_id': self.dealer.id,
        })
        self.assertEqual(experience.experience_name, 'Retail Sales Management')
        self.assertEqual(experience.experience_id.id, self.dealer.id)
        self.assertIn(experience, self.dealer.business_experience_ids)

