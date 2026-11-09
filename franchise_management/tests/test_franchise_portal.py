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
"""Test cases for Franchise Portal controller."""
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestFranchisePortal(HttpCase):
    """Test suite for franchise portal routes (/my/franchise, detail, decline, accept)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agreement = cls.env['franchise.agreement'].create({
            'agreement_type': 'Yearly',
            'agreement_body': '<p>Yearly Agreement</p>',
        })
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal Franchise User',
            'login': 'portal_dealer@example.com',
            'email': 'portal_dealer@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        cls.dealer = cls.env['franchise.dealer'].create({
            'dealer_name': 'Portal Dealer Test',
            'dealer_mail': 'portal_dealer@example.com',
            'monthly_target_amount': 20000.0,
            'contract_type_id': cls.agreement.id,
            'state': 'e_contract',
            'dealer_portal_user': cls.portal_user.id,
        })

    def test_my_franchise_list_page(self):
        """Test GET /my/franchise renders portal list page."""
        self.authenticate('portal_dealer@example.com', 'portal_dealer@example.com')
        response = self.url_open('/my/franchise')
        self.assertEqual(response.status_code, 200)

    def test_my_franchise_detail_page(self):
        """Test GET /my/franchise/<id> renders detail sign page."""
        self.authenticate('portal_dealer@example.com', 'portal_dealer@example.com')
        response = self.url_open(f'/my/franchise/{self.dealer.id}')
        self.assertEqual(response.status_code, 200)

    def test_portal_franchise_decline(self):
        """Test declining contract via POST /my/franchise/<id>/decline."""
        self.authenticate('portal_dealer@example.com', 'portal_dealer@example.com')
        csrf_token = self.csrf_token()
        response = self.url_open(
            f'/my/franchise/{self.dealer.id}/decline',
            data={'csrf_token': csrf_token},
        )
        self.assertEqual(response.status_code, 200)
        self.dealer.invalidate_recordset(['state'])
        self.assertEqual(self.dealer.state, 'g_declined')
