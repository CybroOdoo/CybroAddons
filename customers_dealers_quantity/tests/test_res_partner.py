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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResPartner(TransactionCase):
    """Test cases for dealer field on res.partner."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']

    def test_default_dealer_value(self):
        """Test that dealer field defaults to False."""
        partner = self.Partner.create({'name': 'Regular Customer'})
        self.assertFalse(
            partner.dealer,
            "The dealer field should be False by default."
        )

    def test_create_partner_as_dealer(self):
        """Test creating a partner with dealer set to True."""
        dealer = self.Partner.create({
            'name': 'Test Dealer',
            'dealer': True,
        })
        self.assertTrue(
            dealer.dealer,
            "The dealer field should be True when explicitly set."
        )

    def test_update_dealer_status(self):
        """Test toggling dealer status using write method."""
        partner = self.Partner.create({'name': 'Customer to Dealer'})
        self.assertFalse(partner.dealer)

        partner.write({'dealer': True})
        self.assertTrue(
            partner.dealer,
            "The dealer field should be updated to True."
        )

        partner.write({'dealer': False})
        self.assertFalse(
            partner.dealer,
            "The dealer field should be updated to False."
        )

    def test_search_dealer_partners(self):
        """Test searching partners filtered by dealer field."""
        dealer = self.Partner.create({'name': 'Searchable Dealer', 'dealer': True})
        regular = self.Partner.create({'name': 'Regular Contact', 'dealer': False})

        dealers = self.Partner.search([('id', 'in', [dealer.id, regular.id]), ('dealer', '=', True)])
        self.assertIn(dealer, dealers)
        self.assertNotIn(regular, dealers)
