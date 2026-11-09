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
"""Test cases for Web Franchise Sale feedback controller."""
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestWebFranchiseSale(HttpCase):
    """Test suite for feedback report routes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agreement = cls.env['franchise.agreement'].create({
            'agreement_type': 'Monthly',
            'agreement_body': '<p>Monthly Terms</p>',
        })
        cls.dealer = cls.env['franchise.dealer'].create({
            'dealer_name': 'Feedback Controller Dealer',
            'dealer_mail': 'dealer_feedback_ctl@example.com',
            'monthly_target_amount': 15000.0,
            'contract_type_id': cls.agreement.id,
        })

    def test_feedback_report_menu_get(self):
        """Test GET /feedback_report_menu loads form successfully."""
        response = self.url_open(f'/feedback_report_menu?id={self.dealer.id}')
        self.assertEqual(response.status_code, 200)

    def test_dealer_feedback_form_submit(self):
        """Test POST /dealer_feedback_menu/form/submit creates dealer.sale record."""
        self.authenticate(None, None)
        post_data = {
            'csrf_token': self.csrf_token(),
            'dealer_id': str(self.dealer.id),
            'franchise_reference': 'REF-001',
            'dealer_agreement_id': str(self.agreement.id),
            'sale_quantity': '30',
            'scrap_quantity': '1',
            'total_sale_amount': '14500.0',
            'discount_percentage': '5.0',
            'monthly_target_amount': '15000.0',
            'monthly_target_gained': '96.6',
        }
        response = self.url_open('/dealer_feedback_menu/form/submit', data=post_data)
        self.assertEqual(response.status_code, 200)

        sale_record = self.env['dealer.sale'].search([
            ('dealer_id', '=', self.dealer.id),
            ('franchise_reference', '=', 'REF-001'),
        ])
        self.assertTrue(sale_record, "A dealer.sale record must be created")
        self.assertEqual(sale_record.total_sale_amount, 14500.0)
        self.assertEqual(sale_record.sale_quantity, 30)
