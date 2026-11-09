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
"""Test cases for Franchise Customer Portal controller counter calculations."""
from odoo.tests import TransactionCase, tagged
from odoo.addons.franchise_management.controllers.franchise_customer_portal import FranchiseCustomerPortal


@tagged('post_install', '-at_install')
class TestFranchiseCustomerPortal(TransactionCase):
    """Test suite for Franchise Customer Portal counter calculations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = FranchiseCustomerPortal()
        cls.controller._custom_env = cls.env
        cls.agreement = cls.env['franchise.agreement'].create({
            'agreement_type': 'Monthly',
            'agreement_body': '<p>Terms</p>',
        })
        cls.dealer = cls.env['franchise.dealer'].create({
            'dealer_name': 'Portal Counter Dealer',
            'dealer_mail': 'counter_dealer@example.com',
            'monthly_target_amount': 10000.0,
            'contract_type_id': cls.agreement.id,
            'state': 'e_contract',
        })

    def test_prepare_portal_counter_values(self):
        """Test _prepare_portal_counter_values returns correct model, domain and sudo access."""
        model_name, domain, access = self.controller._prepare_portal_counter_values('franchise_count')
        self.assertEqual(model_name, 'franchise.dealer')
        self.assertEqual(access, 'sudo')
        self.assertTrue(any(item[0] == 'state' for item in domain))

    def test_prepare_home_portal_values(self):
        """Test _prepare_home_portal_values returns franchise_count in values dict."""
        values = self.controller._prepare_home_portal_values(['franchise_count'])
        self.assertIn('franchise_count', values)
        self.assertGreaterEqual(values['franchise_count'], 1)
