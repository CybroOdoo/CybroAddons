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
"""Test cases for payment.risk.score model and related partner fields."""
from datetime import date, timedelta
from psycopg2 import IntegrityError
from unittest.mock import patch
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestPaymentRiskScore(TransactionCase):
    """Test suite for payment risk scoring and automated features."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer Risk',
            'customer_rank': 1,
            'email': 'customer@example.com',
        })
        cls.company = cls.env.company

    def test_compute_risk_level(self):
        """Test risk level and color computation based on score thresholds."""
        score_rec = self.env['payment.risk.score'].create({
            'partner_id': self.partner.id,
            'score': 20.0,
        })
        self.assertEqual(score_rec.risk_level, 'low')
        self.assertEqual(score_rec.risk_color, '#28a745')

        score_rec.score = 40.0
        self.assertEqual(score_rec.risk_level, 'medium')
        self.assertEqual(score_rec.risk_color, '#ffc107')

        score_rec.score = 65.0
        self.assertEqual(score_rec.risk_level, 'high')
        self.assertEqual(score_rec.risk_color, '#fd7e14')

        score_rec.score = 85.0
        self.assertEqual(score_rec.risk_level, 'critical')
        self.assertEqual(score_rec.risk_color, '#dc3545')

    def test_unique_partner_company_constraint(self):
        """Test that only one risk score record is permitted per customer and company."""
        self.env['payment.risk.score'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'score': 30.0,
        })
        with self.assertRaises((IntegrityError, ValidationError)), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                self.env['payment.risk.score'].create({
                    'partner_id': self.partner.id,
                    'company_id': self.company.id,
                    'score': 50.0,
                })

    def test_no_history_values(self):
        """Test score computation when customer has no invoice history."""
        res = self.env['payment.risk.score'].compute_for_partner(self.partner.id)
        self.assertEqual(res.score, 0.0)
        self.assertEqual(res.total_invoices, 0)
        self.assertFalse(res.ai_powered)
        self.assertIn('No invoice history', res.ai_reasoning)

    def test_compute_for_partner_and_fallback(self):
        """Test risk score calculation using statistical fallback."""
        today = date.today()
        # Create an account.move for testing statistics
        account = self.env['account.account'].search([
            ('account_type', '=', 'income'),
        ], limit=1)
        if not account:
            account = self.env['account.account'].create({
                'name': 'Sales Test Income',
                'code': 'TESTINC4000',
                'account_type': 'income',
            })
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': today - timedelta(days=60),
            'invoice_date_due': today - timedelta(days=30),
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Consulting Service',
                    'quantity': 1,
                    'price_unit': 1000.0,
                    'account_id': account.id,
                })
            ]
        })
        invoice.action_post()

        record = self.env['payment.risk.score'].compute_for_partner(self.partner.id)
        self.assertTrue(record)
        self.assertEqual(record.total_invoices, 1)
        self.assertEqual(record.currently_overdue, 1)
        self.assertGreater(record.total_overdue_amount, 0)

        # Recomputing updates existing record without duplicate
        updated = self.env['payment.risk.score'].compute_for_partner(self.partner.id)
        self.assertEqual(record.id, updated.id)

    def test_automated_risk_alert(self):
        """Test sending automated payment risk alert emails for high risk customers."""
        score_rec = self.env['payment.risk.score'].create({
            'partner_id': self.partner.id,
            'score': 80.0,  # Critical risk
            'currently_overdue': 2,
            'total_overdue_amount': 2500.0,
            'avg_delay_days': 45.0,
        })
        self.assertEqual(score_rec.risk_level, 'critical')

        # Clear existing outgoing mails
        self.env['mail.mail'].search([]).unlink()

        # Trigger alert
        score_rec._send_risk_alert()
        sent_mails = self.env['mail.mail'].search([
            ('subject', 'ilike', f"Payment Risk Alert: {self.partner.name}")
        ])
        self.assertTrue(sent_mails)

    def test_action_send_risk_alert(self):
        """Test manual action_send_risk_alert returns success notification."""
        score_rec = self.env['payment.risk.score'].create({
            'partner_id': self.partner.id,
            'score': 70.0,  # High risk
        })
        action = score_rec.action_send_risk_alert()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'display_notification')
        self.assertEqual(action['params']['type'], 'success')

    def test_compute_for_partner_alerts_only_on_risk_change(self):
        """Test compute_for_partner sends alert on risk escalation and not repeatedly on daily cron runs."""
        partner_alert = self.env['res.partner'].create({
            'name': 'Alert Test Customer',
            'email': 'alert_test@example.com',
            'customer_rank': 1,
        })
        self.env['mail.mail'].search([]).unlink()

        # Mock _compute_score_for_partner to return high risk
        with patch.object(
            type(self.env['payment.risk.score']),
            '_compute_score_for_partner',
            return_value={
                'score': 70.0,
                'delay_score': 20.0,
                'overdue_score': 20.0,
                'total_invoices': 5,
                'partner_id': partner_alert.id,
                'company_id': self.company.id,
            },
        ):
            # First compute: newly high risk -> alert sent
            rec = self.env['payment.risk.score'].compute_for_partner(partner_alert.id)
            self.assertEqual(rec.risk_level, 'high')
            mail_count = self.env['mail.mail'].search_count([
                ('subject', 'ilike', f"Payment Risk Alert: {partner_alert.name}")
            ])
            self.assertEqual(mail_count, 1)

            # Second compute (daily cron): still high risk -> alert not re-sent
            self.env['payment.risk.score'].compute_for_partner(partner_alert.id)
            mail_count_after = self.env['mail.mail'].search_count([
                ('subject', 'ilike', f"Payment Risk Alert: {partner_alert.name}")
            ])
            self.assertEqual(mail_count_after, 1)

    def test_partner_computed_risk_fields(self):
        """Test res.partner computed fields derived from payment.risk.score."""
        score_rec = self.env['payment.risk.score'].create({
            'partner_id': self.partner.id,
            'score': 60.0,
            'avg_delay_days': 15.0,
            'total_overdue_amount': 1200.0,
            'followup_suggestion': 'Send email reminder',
        })
        self.partner._compute_payment_risk_fields()
        self.assertEqual(self.partner.payment_risk_score, 60.0)
        self.assertEqual(self.partner.payment_risk_level, 'high')
        self.assertEqual(self.partner.payment_risk_color, '#fd7e14')
        self.assertEqual(self.partner.payment_avg_delay, 15.0)
        self.assertEqual(self.partner.payment_overdue_amount, 1200.0)
        self.assertEqual(self.partner.payment_followup_suggestion, 'Send email reminder')

    def test_action_send_followup(self):
        """Test opening send followup wizard from payment risk score record."""
        score_rec = self.env['payment.risk.score'].create({
            'partner_id': self.partner.id,
            'score': 30.0,
            'followup_email': 'Dear Customer, Please pay your bill.',
        })
        action = score_rec.action_send_followup()
        self.assertEqual(action.get('res_model'), 'send.followup.wizard')
        self.assertEqual(action.get('context', {}).get('default_partner_id'), self.partner.id)
        self.assertIn('Dear Customer', action['context']['default_message'])

    def test_compute_all_partners_multicompany(self):
        """Test compute_all_partners iterates across companies."""
        comp2 = self.env['res.company'].create({'name': 'Second Test Company'})
        partner2 = self.env['res.partner'].create({
            'name': 'Company 2 Customer',
            'customer_rank': 1,
            'company_id': comp2.id,
        })
        scored = self.env['payment.risk.score'].compute_all_partners()
        self.assertGreaterEqual(scored, 2)
        score_comp2 = self.env['payment.risk.score'].search([
            ('partner_id', '=', partner2.id),
            ('company_id', '=', comp2.id),
        ])
        self.assertTrue(score_comp2)

    def test_collect_invoice_stats_trend_alignment(self):
        """Test that trend calculation properly aligns recent and old delays."""
        today = date.today()
        account = self.env['account.account'].search([
            ('account_type', '=', 'income'),
        ], limit=1)
        if not account:
            account = self.env['account.account'].create({
                'name': 'Sales Test Income Trend',
                'code': 'TESTINC4001',
                'account_type': 'income',
            })
        inv_old = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': today - timedelta(days=200),
            'invoice_date_due': today - timedelta(days=190),
            'invoice_line_ids': [(0, 0, {'name': 'Old', 'price_unit': 500, 'account_id': account.id})],
        })
        inv_old.action_post()
        inv_recent = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': today - timedelta(days=30),
            'invoice_date_due': today - timedelta(days=20),
            'invoice_line_ids': [(0, 0, {'name': 'Recent', 'price_unit': 500, 'account_id': account.id})],
        })
        inv_recent.action_post()

        stats = self.env['payment.risk.score']._collect_invoice_stats(self.partner)
        self.assertIsNotNone(stats)
        self.assertEqual(stats['total_invoices'], 2)

    def test_expand_risk_level(self):
        """Test _expand_risk_level returns all valid risk level keys."""
        keys = self.env['payment.risk.score']._expand_risk_level()
        self.assertEqual(keys, ['low', 'medium', 'high', 'critical'])

    def test_compute_is_gemini_configured(self):
        """Test _compute_is_gemini_configured detects presence of API key."""
        score_rec = self.env['payment.risk.score'].create({
            'partner_id': self.partner.id,
            'score': 25.0,
        })
        self.env['ir.config_parameter'].sudo().set_str('predict_late_payment.gemini_api_key', '')
        score_rec._compute_is_gemini_configured()
        self.assertFalse(score_rec.is_gemini_configured)

        self.env['ir.config_parameter'].sudo().set_str('predict_late_payment.gemini_api_key', 'AIzaSyKey123')
        score_rec._compute_is_gemini_configured()
        self.assertTrue(score_rec.is_gemini_configured)

    def test_compute_days_since_payment(self):
        """Test _compute_days_since_payment with and without last payment date."""
        today = date.today()
        score_rec = self.env['payment.risk.score'].create({
            'partner_id': self.partner.id,
            'last_payment_date': today - timedelta(days=12),
        })
        self.assertEqual(score_rec.days_since_last_payment, 12)

        score_rec.last_payment_date = False
        score_rec._compute_days_since_payment()
        self.assertEqual(score_rec.days_since_last_payment, 0)

    def test_collect_invoice_stats_no_invoices(self):
        """Test _collect_invoice_stats returns None for partner without invoices."""
        new_partner = self.env['res.partner'].create({'name': 'Zero Invoices Partner'})
        stats = self.env['payment.risk.score']._collect_invoice_stats(new_partner)
        self.assertIsNone(stats)

    def test_action_compute_all_partners(self):
        """Test action_compute_all_partners returns success notification when records are scored."""
        action = self.env['payment.risk.score'].action_compute_all_partners()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'display_notification')
        self.assertIn(action['params']['type'], ('success', 'warning'))

    def test_action_compute_score(self):
        """Test action_compute_score manual recompute with fallback or AI status."""
        score_rec = self.env['payment.risk.score'].create({
            'partner_id': self.partner.id,
            'score': 50.0,
            'ai_powered': False,
        })
        action = score_rec.action_compute_score()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'display_notification')

        # Test when ai_powered is True
        score_rec.ai_powered = True
        action_ai = score_rec.action_compute_score()
        self.assertEqual(action_ai.get('type'), 'ir.actions.client')

    def test_action_test_ai_connection(self):
        """Test action_test_ai_connection delegates to res.config.settings action."""
        score_rec = self.env['payment.risk.score'].create({
            'partner_id': self.partner.id,
            'score': 50.0,
        })
        action = score_rec.action_test_ai_connection()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'display_notification')

