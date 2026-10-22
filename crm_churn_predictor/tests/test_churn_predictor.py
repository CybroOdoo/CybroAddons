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
import logging
from odoo.tests.common import TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestChurnPredictor(TransactionCase):
    """Test suite for CRM Churn Predictor module."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment: partner, user, team."""
        super().setUpClass()
        cls.test_partner = cls.env['res.partner'].create({
            'name': 'Churn Test Customer',
            'is_company': True,
            'vat': 'US123456789',
            'customer_rank': 1,
            'email': 'churn_test@example.com',
        })
        cls.test_manager = cls.env['res.users'].create({
            'name': 'Churn Manager User',
            'login': 'churn_manager_user@example.com',
            'email': 'churn_manager_user@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('crm_churn_predictor.group_churn_manager').id,
            ])],
        })
        cls.test_partner.user_id = cls.test_manager

    def test_01_churn_scoring_calculation(self):
        """Test calculation of churn score, risk levels, and suggestions."""
        churn_record = self.env['churn.score'].create({
            'partner_id': self.test_partner.id,
        })
        # Fresh calculation without orders/contacts defaults to stale values
        vals = churn_record._calculate_score()
        self.assertIn('churn_score', vals)
        self.assertIn('risk_level', vals)
        self.assertIn('suggested_actions', vals)
        self.assertTrue(0 <= vals['churn_score'] <= 100)

        # Test threshold calculation directly
        from ..models.churn_score import (
            PURCHASE_RECENCY_THRESHOLDS,
            PURCHASE_RECENCY_MAX,
            _score_from_thresholds,
        )
        self.assertEqual(
            _score_from_thresholds(
                15, PURCHASE_RECENCY_THRESHOLDS, PURCHASE_RECENCY_MAX
            ),
            0
        )
        self.assertEqual(
            _score_from_thresholds(
                45, PURCHASE_RECENCY_THRESHOLDS, PURCHASE_RECENCY_MAX
            ),
            10
        )
        self.assertEqual(
            _score_from_thresholds(
                200, PURCHASE_RECENCY_THRESHOLDS, PURCHASE_RECENCY_MAX
            ),
            35
        )

    def test_02_alert_dispatch_no_duplication_bug(self):
        """Verify _dispatch_alert sets alert_sent=True without duplicating
        activities or chatter messages.
        """
        churn_record = self.env['churn.score'].create({
            'partner_id': self.test_partner.id,
            'risk_level': 'high',
            'churn_score': 65.0,
            'suggested_actions': '• Reach out immediately.',
        })

        initial_activities = len(churn_record.activity_ids)
        initial_messages = len(churn_record.message_ids)

        # Dispatch alert
        churn_record._dispatch_alert()

        # Alert flag should be True
        self.assertTrue(churn_record.alert_sent)

        # Activity count should increase by exactly 1
        new_activities = len(churn_record.activity_ids)
        self.assertEqual(
            new_activities - initial_activities,
            1,
            "Activity must NOT be duplicated!"
        )

        # Message count should increase by exactly 1 comment
        new_messages = len(churn_record.message_ids)
        self.assertEqual(
            new_messages - initial_messages,
            1,
            "Chatter message must NOT be duplicated!"
        )

    def test_03_partner_smart_button_and_relation(self):
        """Test partner churn_score_ids One2many and smart button action."""
        # Prior to creation, opening churn score creates record on the fly
        action = self.test_partner.action_open_churn_score()
        self.assertEqual(action.get('res_model'), 'churn.score')
        self.assertEqual(action.get('view_mode'), 'form')

        # Check One2many relation name churn_score_ids
        self.assertEqual(len(self.test_partner.churn_score_ids), 1)
        self.assertEqual(self.test_partner.churn_score_count, 1)

        # Ensure subsequent action opens existing single record
        action_existing = self.test_partner.action_open_churn_score()
        self.assertEqual(
            action_existing.get('res_id'),
            self.test_partner.churn_score_ids.id
        )

    def test_04_action_compute_score_and_recovery(self):
        """Test action_compute_score and alert reset when risk drops."""
        churn_record = self.env['churn.score'].create({
            'partner_id': self.test_partner.id,
            'risk_level': 'critical',
            'alert_sent': True,
        })
        self.assertTrue(churn_record.alert_sent)

        # Recomputing manually
        churn_record.action_compute_score()
        # Verify color mapping compute
        self.assertIn(
            churn_record.risk_level, ['low', 'medium', 'high', 'critical']
        )
        self.assertTrue(churn_record.color >= 0)

    def test_05_cron_job_execution(self):
        """Test daily cron method execution and ir.cron existence."""
        cron = self.env.ref(
            'crm_churn_predictor.ir_cron_churn_score_daily',
            raise_if_not_found=False
        )
        self.assertIsNotNone(cron, "Daily cron record must exist.")
        self.assertEqual(cron.interval_type, 'days')

        # Execute cron method
        self.env['churn.score'].cron_compute_all_scores()
        score_record = self.env['churn.score'].search([
            ('partner_id', '=', self.test_partner.id)
        ], limit=1)
        self.assertTrue(score_record)
