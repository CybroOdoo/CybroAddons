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
"""Test suite for res.partner payment risk extensions."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResPartnerPaymentRisk(TransactionCase):
    """Test suite covering payment risk computations and actions on res.partner."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Partner Extension Test Customer',
            'customer_rank': 1,
            'email': 'partner_ext@example.com',
        })

    def test_compute_currency(self):
        """Test _compute_currency sets the company currency."""
        self.partner._compute_currency()
        self.assertEqual(self.partner.currency_id, self.company.currency_id)

    def test_compute_payment_risk_fields_without_score(self):
        """Test risk fields default to zero / empty when no risk record exists."""
        self.partner._compute_payment_risk_fields()
        self.assertEqual(self.partner.payment_risk_score, 0.0)
        self.assertFalse(self.partner.payment_risk_level)
        self.assertEqual(self.partner.payment_risk_color, '#6c757d')
        self.assertEqual(self.partner.payment_avg_delay, 0.0)
        self.assertEqual(self.partner.payment_overdue_amount, 0.0)
        self.assertFalse(self.partner.payment_last_computed)
        self.assertFalse(self.partner.payment_followup_suggestion)

    def test_compute_payment_risk_fields_with_score(self):
        """Test risk fields reflect values from the partner's risk score record."""
        score_rec = self.env['payment.risk.score'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'score': 72.0,
            'avg_delay_days': 20.5,
            'total_overdue_amount': 3400.0,
            'followup_suggestion': 'Urgent call required',
        })
        self.partner._compute_payment_risk_fields()
        self.assertEqual(self.partner.payment_risk_score, 72.0)
        self.assertEqual(self.partner.payment_risk_level, 'high')
        self.assertEqual(self.partner.payment_risk_color, '#fd7e14')
        self.assertEqual(self.partner.payment_avg_delay, 20.5)
        self.assertEqual(self.partner.payment_overdue_amount, 3400.0)
        self.assertEqual(self.partner.payment_followup_suggestion, 'Urgent call required')

    def test_action_compute_risk_score(self):
        """Test button action action_compute_risk_score calculates score and returns notification."""
        action = self.partner.action_compute_risk_score()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'display_notification')
        self.assertEqual(action['params']['type'], 'success')

        score_rec = self.env['payment.risk.score'].search([
            ('partner_id', '=', self.partner.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertTrue(score_rec)

    def test_action_view_risk_score(self):
        """Test action_view_risk_score opens existing score form or computes new."""
        # 1. Without pre-existing score
        action = self.partner.action_view_risk_score()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'payment.risk.score')
        self.assertTrue(action.get('res_id'))

        # 2. With existing score
        action_existing = self.partner.action_view_risk_score()
        self.assertEqual(action_existing.get('res_id'), action.get('res_id'))

    def test_invoice_user_can_compute_and_view_risk_score(self):
        """Test invoice user with read-only risk score access can click compute and view buttons."""
        invoice_group = self.env.ref('account.group_account_invoice')
        user = self.env['res.users'].create({
            'name': 'Invoice User Res Partner',
            'login': 'invoice_user_partner_test',
            'email': 'invoice_user_partner@example.com',
            'group_ids': [(6, 0, [invoice_group.id, self.env.ref('base.group_user').id])],
        })
        partner = self.partner.with_user(user)
        action_compute = partner.action_compute_risk_score()
        self.assertEqual(action_compute.get('params', {}).get('type'), 'success')

        action_view = partner.action_view_risk_score()
        self.assertEqual(action_view.get('res_model'), 'payment.risk.score')
        self.assertTrue(action_view.get('res_id'))
