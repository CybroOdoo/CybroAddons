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
"""Test cases for Dealer Sale Report Wizard."""
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDealerSaleReport(TransactionCase):
    """Test suite for dealer.sale.report wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        standard_layout = cls.env.ref('web.external_layout_standard', raise_if_not_found=False)
        if standard_layout:
            cls.env.company.external_report_layout_id = standard_layout
        cls.agreement = cls.env['franchise.agreement'].create({
            'agreement_type': 'Monthly',
            'agreement_body': '<p>Monthly Agreement</p>',
        })
        cls.dealer = cls.env['franchise.dealer'].create({
            'dealer_name': 'Sale Report Dealer',
            'dealer_mail': 'sale_report_dealer@example.com',
            'monthly_target_amount': 25000.0,
            'contract_type_id': cls.agreement.id,
            'company_id': cls.env.company.id,
        })
        cls.sale = cls.env['dealer.sale'].create({
            'dealer_id': cls.dealer.id,
            'dealer_agreement_id': cls.agreement.id,
            'sale_quantity': 100,
            'scrap_quantity': 5,
            'total_sale_amount': 24000.0,
            'monthly_target_amount': 25000.0,
            'monthly_target_gained': 96.0,
            'company_id': cls.env.company.id,
        })

    def _get_report_action(self, action):
        """Helper to extract underlying report action if wrapped in layout wizard."""
        if action.get('type') == 'ir.actions.act_window':
            return action.get('context', {}).get('report_action', action)
        return action

    def test_sale_report_no_data_raises_user_error(self):
        """Test UserError is raised when no matching sales data is found."""
        other_dealer = self.env['franchise.dealer'].create({
            'dealer_name': 'No Sale Dealer',
            'dealer_mail': 'no_sale@example.com',
            'monthly_target_amount': 1000.0,
            'contract_type_id': self.agreement.id,
            'company_id': self.env.company.id,
        })
        wizard = self.env['dealer.sale.report'].create({
            'dealer_id': other_dealer.id,
        })
        with self.assertRaises(UserError):
            wizard.create_report()

    def test_sale_report_dealer_based(self):
        """Test generating sales report filtered by dealer_id."""
        wizard = self.env['dealer.sale.report'].create({
            'type': 'dealer_based',
            'dealer_id': self.dealer.id,
        })
        action = self._get_report_action(wizard.create_report())
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_name'), 'franchise_management.dealer_sale_on_dealer_report_pdf')

    def test_sale_report_agreement_based(self):
        """Test generating sales report filtered by agreement_id."""
        wizard = self.env['dealer.sale.report'].create({
            'type': 'agreement_based',
            'agreement_id': self.agreement.id,
        })
        action = self._get_report_action(wizard.create_report())
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_name'), 'franchise_management.dealer_sale_on_agreement_report_pdf')

    def test_sale_report_all(self):
        """Test generating sales report without filters."""
        wizard = self.env['dealer.sale.report'].create({})
        action = self._get_report_action(wizard.create_report())
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_name'), 'franchise_management.all_dealer_sale_report_pdf')
