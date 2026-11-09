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
"""Test cases for Dealer Report Wizard."""
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDealerReport(TransactionCase):
    """Test suite for dealer.report wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        standard_layout = cls.env.ref('web.external_layout_standard', raise_if_not_found=False)
        if standard_layout:
            cls.env.company.external_report_layout_id = standard_layout
        cls.agreement = cls.env['franchise.agreement'].create({
            'agreement_type': 'Yearly',
            'agreement_body': '<p>Yearly</p>',
        })
        cls.dealer_user = cls.env['res.users'].create({
            'name': 'Report Dealer User',
            'login': 'report_dealer_user@example.com',
            'email': 'report_dealer_user@example.com',
            'is_dealer_user': True,
        })
        cls.dealer = cls.env['franchise.dealer'].create({
            'dealer_name': 'Report Dealer',
            'dealer_mail': 'report_dealer_user@example.com',
            'monthly_target_amount': 15000.0,
            'contract_type_id': cls.agreement.id,
            'dealer_portal_user': cls.dealer_user.id,
            'company_id': cls.env.company.id,
        })

    def _get_report_action(self, action):
        """Helper to extract underlying report action if wrapped in layout wizard."""
        if action.get('type') == 'ir.actions.act_window':
            return action.get('context', {}).get('report_action', action)
        return action

    def test_report_no_data_raises_user_error(self):
        """Test UserError is raised when no matching data found."""
        other_user = self.env['res.users'].create({
            'name': 'Unused User',
            'login': 'unused_user@example.com',
            'is_dealer_user': True,
        })
        wizard = self.env['dealer.report'].create({
            'dealer_id': other_user.id,
        })
        with self.assertRaises(UserError):
            wizard.create_report()

    def test_report_dealer_based(self):
        """Test generating report filtered by dealer_id."""
        wizard = self.env['dealer.report'].create({
            'type': 'dealer_based',
            'dealer_id': self.dealer_user.id,
        })
        action = self._get_report_action(wizard.create_report())
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_name'), 'franchise_management.dealer_based_report_pdf')

    def test_report_agreement_based(self):
        """Test generating report filtered by agreement_id."""
        wizard = self.env['dealer.report'].create({
            'type': 'agreement_based',
            'agreement_id': self.agreement.id,
        })
        action = self._get_report_action(wizard.create_report())
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_name'), 'franchise_management.agreement_based_report_pdf')

    def test_report_all_dealers(self):
        """Test generating report without dealer/agreement filters."""
        wizard = self.env['dealer.report'].create({})
        action = self._get_report_action(wizard.create_report())
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_name'), 'franchise_management.all_dealer_based_report_pdf')
