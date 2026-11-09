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
"""Test cases for Dealer Sales model."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDealerSale(TransactionCase):
    """Test suite for dealer.sale model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agreement = cls.env['franchise.agreement'].create({
            'agreement_type': 'Monthly',
            'agreement_body': '<p>Agreement Body</p>',
        })
        cls.dealer = cls.env['franchise.dealer'].create({
            'dealer_name': 'Sales Dealer',
            'dealer_mail': 'sales_dealer@test.com',
            'monthly_target_amount': 20000.0,
            'contract_type_id': cls.agreement.id,
        })
        cls.sale = cls.env['dealer.sale'].create({
            'dealer_id': cls.dealer.id,
            'dealer_agreement_id': cls.agreement.id,
            'sale_quantity': 50,
            'scrap_quantity': 2,
            'total_sale_amount': 18000.0,
            'discount_percentage': 5.0,
            'monthly_target_amount': 20000.0,
            'monthly_target_gained': 90.0,
        })

    def test_dealer_sale_creation(self):
        """Test dealer sale record creation, sequence and defaults."""
        self.assertEqual(self.sale.state, 'a_to_verify')
        self.assertTrue(self.sale.serial_no)
        self.assertNotEqual(self.sale.serial_no, 'New')
        self.assertEqual(self.sale.dealer_id, self.dealer)
        self.assertEqual(self.sale.total_sale_amount, 18000.0)

    def test_action_verify_sale(self):
        """Test verifying the dealer sale record."""
        self.sale.action_verify_sale()
        self.assertEqual(self.sale.state, 'b_verified')

