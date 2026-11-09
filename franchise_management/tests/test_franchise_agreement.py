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
"""Test cases for Franchise Agreement model."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFranchiseAgreement(TransactionCase):
    """Test suite for franchise.agreement model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agreement_monthly = cls.env['franchise.agreement'].create({
            'agreement_type': 'Monthly',
            'agreement_body': '<p>Monthly Agreement Body</p>',
        })
        cls.agreement_yearly = cls.env['franchise.agreement'].create({
            'agreement_type': 'Yearly',
            'agreement_body': '<p>Yearly Agreement Body</p>',
        })

    def test_agreement_creation(self):
        """Test agreement creation and fields values."""
        self.assertEqual(self.agreement_monthly.agreement_type, 'Monthly')
        self.assertEqual(self.agreement_monthly.agreement_body, '<p>Monthly Agreement Body</p>')
        self.assertEqual(self.agreement_yearly.agreement_type, 'Yearly')

    def test_agreement_rec_name(self):
        """Test rec_name returns agreement_type."""
        self.assertEqual(self.agreement_monthly.display_name, 'Monthly')
        self.assertEqual(self.agreement_yearly.display_name, 'Yearly')

