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
"""Test cases for Web Franchise Dealer controller."""
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestWebFranchiseDealer(HttpCase):
    """Test suite for /franchise_menu and form submission routes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agreement = cls.env['franchise.agreement'].create({
            'agreement_type': 'Yearly',
            'agreement_body': '<p>Terms and Conditions</p>',
        })

    def test_franchise_menu_get(self):
        """Test GET /franchise_menu returns 200 and loads dealer application form."""
        response = self.url_open('/franchise_menu')
        self.assertEqual(response.status_code, 200)

    def test_franchise_menu_form_submit(self):
        """Test POST /franchise_menu/form/submit creates franchise dealer."""
        self.authenticate(None, None)
        post_data = {
            'csrf_token': self.csrf_token(),
            'franchisee_name': 'Web Applicant',
            'franchisee_email': 'applicant@webexample.com',
            'dealer_phone': '9876543210',
            'dealer_mobile': '9876543210',
            'monthly_target_amount': '12000.0',
            'contract_type_id': str(self.agreement.id),
            'city': 'San Francisco',
            'business_city': 'San Francisco',
            'experience': '5 years in retail',
            'site_type': 'owned',
            'site_area': '1500',
            'investment_from': '50000',
            'investment_to': '100000',
        }
        response = self.url_open('/franchise_menu/form/submit', data=post_data)
        self.assertEqual(response.status_code, 200)

        created_dealer = self.env['franchise.dealer'].search([
            ('dealer_mail', '=', 'applicant@webexample.com'),
        ])
        self.assertTrue(created_dealer, "A franchise.dealer record must be created")
        self.assertEqual(created_dealer.dealer_name, 'Web Applicant')
        self.assertEqual(created_dealer.monthly_target_amount, 12000.0)
