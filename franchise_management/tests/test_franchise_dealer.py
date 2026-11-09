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
"""Test cases for Franchise Dealer model."""
from datetime import date, timedelta
from unittest.mock import patch
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFranchiseDealer(TransactionCase):
    """Test suite for franchise.dealer model."""

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
        cls.dealer = cls.env['franchise.dealer'].create({
            'dealer_name': 'John Doe',
            'dealer_mail': 'johndoe@testexample.com',
            'dealer_phone': '1234567890',
            'monthly_target_amount': 10000.0,
            'contract_type_id': cls.agreement_monthly.id,
            'street': '123 Main Street',
            'zip': '12345',
        })

    def test_dealer_creation_and_defaults(self):
        """Test dealer creation, sequence generation and default state."""
        self.assertEqual(self.dealer.state, 'a_draft')
        self.assertNotEqual(self.dealer.serial_no, 'New')
        self.assertTrue(self.dealer.serial_no)
        self.assertEqual(self.dealer.body_html, '<p>Monthly Agreement Body</p>')
        self.assertEqual(self.dealer.access_url, f'/my/franchise/{self.dealer.id}')

    def test_monthly_target_amount_constrains(self):
        """Test UserError raised when monthly_target_amount is 0."""
        with self.assertRaises(UserError):
            self.env['franchise.dealer'].create({
                'dealer_name': 'Zero Target Dealer',
                'dealer_mail': 'zero@test.com',
                'monthly_target_amount': 0.0,
                'contract_type_id': self.agreement_monthly.id,
            })

    def test_state_transitions(self):
        """Test action buttons and state transitions."""
        self.dealer.action_confirm()
        self.assertEqual(self.dealer.state, 'b_to_approve')

        self.dealer.action_approve()
        self.assertEqual(self.dealer.state, 'c_approve')

        self.dealer.action_cancel()
        self.assertEqual(self.dealer.state, 'd_cancel')

        self.dealer.contract_signed()
        self.assertEqual(self.dealer.state, 'f_signed')

        self.dealer.contract_declined()
        self.assertEqual(self.dealer.state, 'g_declined')

    def test_compute_renewal_date_monthly(self):
        """Test renewal date computation for monthly agreement."""
        today = date.today()
        self.dealer.write({
            'signed_on': today,
            'contract_type_id': self.agreement_monthly.id,
        })
        self.assertEqual(self.dealer.contract_renewal_date, today + timedelta(days=30))

    def test_compute_renewal_date_yearly(self):
        """Test renewal date computation for yearly agreement."""
        today = date.today()
        self.dealer.write({
            'signed_on': today,
            'contract_type_id': self.agreement_yearly.id,
        })
        self.assertEqual(self.dealer.contract_renewal_date, today + timedelta(days=365))

    def test_create_portal_user(self):
        """Test creating a portal user from the dealer."""
        user = self.dealer.create_portal_user()
        self.assertTrue(user)
        self.assertEqual(user.login, self.dealer.dealer_mail)
        self.assertEqual(user.email, self.dealer.dealer_mail)
        self.assertEqual(self.dealer.dealer_portal_user, user)
        self.assertTrue(user.has_group('base.group_portal'))

    def test_action_preview_dealer_order(self):
        """Test action_preview_dealer_order returns act_url dict."""
        self.dealer.url = 'http://localhost:8020/my/franchise/1'
        res = self.dealer.action_preview_dealer_order()
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        self.assertEqual(res.get('url'), self.dealer.url)

    def test_action_dealer_feedback(self):
        """Test action_dealer_feedback returns act_window dict."""
        res = self.dealer.action_dealer_feedback()
        self.assertEqual(res.get('type'), 'ir.actions.act_window')
        self.assertEqual(res.get('res_model'), 'dealer.sale')

    def test_action_send_feedback(self):
        """Test action_send_feedback generates feedback_url and executes."""
        with patch.object(type(self.env['mail.template']), 'send_mail', return_value=True):
            res = self.dealer.action_send_feedback()
            self.assertTrue(res)
            self.assertTrue(self.dealer.feedback_url)
            self.assertIn('/@/feedback_report_menu?id=', self.dealer.feedback_url)
