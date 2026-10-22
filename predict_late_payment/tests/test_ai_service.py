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
"""Test suite for payment.risk.ai.service."""
import io
import json
import urllib.error
from unittest.mock import patch
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPaymentRiskAIService(TransactionCase):
    """Test suite covering Google Gemini AI service and statistical fallback."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ai_service = cls.env['payment.risk.ai.service']
        cls.partner = cls.env['res.partner'].create({
            'name': 'AI Test Partner',
            'customer_rank': 1,
            'email': 'ai_test@example.com',
        })
        cls.dummy_stats = {
            'total_invoices': 10,
            'paid_on_time': 8,
            'paid_late': 2,
            'avg_delay_days': 5.0,
            'max_delay_days': 20.0,
            'std_dev_delays': 4.0,
            'overdue_ratio': 10.0,
            'currently_overdue': 1,
            'total_overdue_amount': 500.0,
            'avg_invoice_amount': 1000.0,
            'recent_total': 3,
            'recent_avg_delay': 2.0,
            'trend_delta': -3.0,
            'first_invoice_date': '2025-01-01',
            'paid_invoice_history': [
                {
                    'name': 'INV/2025/001',
                    'due_date': '2025-01-15',
                    'paid_date': '2025-01-20',
                    'delay_days': 5,
                    'amount': 1000.0,
                }
            ],
            'overdue_invoices': [
                {
                    'name': 'INV/2025/002',
                    'due_date': '2025-02-01',
                    'amount': 500.0,
                    'days_overdue': 10,
                }
            ],
        }

    def test_get_param(self):
        """Test _get_param retrieves configured or default value."""
        self.assertEqual(
            self.ai_service._get_param('predict_late_payment.non_existent_key', default='fallback_val'),
            'fallback_val'
        )
        self.env['ir.config_parameter'].sudo().set_str('predict_late_payment.test_param', 'stored_val')
        self.assertEqual(
            self.ai_service._get_param('predict_late_payment.test_param'),
            'stored_val'
        )

    def test_get_model(self):
        """Test _get_model returns configured model or falls back for deprecated models."""
        config_sudo = self.env['ir.config_parameter'].sudo()
        config_sudo.set_str('predict_late_payment.gemini_model', 'gemini-3.6-pro')
        self.assertEqual(self.ai_service._get_model(), 'gemini-3.6-pro')

        # Test deprecated model fallback
        config_sudo.set_str('predict_late_payment.gemini_model', 'gemini-2.5-flash')
        self.assertEqual(self.ai_service._get_model(), 'gemini-3.6-flash')

        config_sudo.set_str('predict_late_payment.gemini_model', '')
        self.assertEqual(self.ai_service._get_model(), 'gemini-3.6-flash')

    def test_fallback_score(self):
        """Test _fallback_score calculation logic."""
        res = self.ai_service._fallback_score(self.dummy_stats)
        self.assertIn('score', res)
        self.assertIn('risk_level', res)
        self.assertIn('delay_score', res)
        self.assertIn('overdue_score', res)
        self.assertIn('suggested_credit_limit', res)
        self.assertGreater(res['suggested_credit_limit'], 0)
        self.assertIn('Statistical fallback', res['ai_reasoning'])

    def test_build_prompt(self):
        """Test _build_prompt generates formatted prompt containing customer stats."""
        prompt = self.ai_service._build_prompt(self.partner, self.dummy_stats)
        self.assertIn(self.partner.name, prompt)
        self.assertIn('PAYMENT STATISTICS', prompt)
        self.assertIn('INV/2025/001', prompt)
        self.assertIn('INV/2025/002', prompt)

    def test_parse_response(self):
        """Test _parse_response parses JSON and calculates risk levels across thresholds."""
        # 1. Low risk
        sample_json_low = json.dumps({
            'score': 15.0,
            'suggested_credit_limit': 5000.0,
            'delay_score': 5.0,
        })
        parsed_low = self.ai_service._parse_response(sample_json_low)
        self.assertEqual(parsed_low['score'], 15.0)
        self.assertEqual(parsed_low['risk_level'], 'low')

        # 2. Medium risk
        sample_json_med = json.dumps({'score': 35.0, 'suggested_credit_limit': 3000.0})
        self.assertEqual(self.ai_service._parse_response(sample_json_med)['risk_level'], 'medium')

        # 3. High risk
        sample_json_high = json.dumps({'score': 65.0, 'suggested_credit_limit': 1000.0})
        self.assertEqual(self.ai_service._parse_response(sample_json_high)['risk_level'], 'high')

        # 4. Critical risk
        sample_json_crit = json.dumps({'score': 90.0, 'suggested_credit_limit': 0.0})
        self.assertEqual(self.ai_service._parse_response(sample_json_crit)['risk_level'], 'critical')

    def test_analyze_customer_without_api_key(self):
        """Test analyze_customer falls back to statistical rules when key is missing."""
        self.env['ir.config_parameter'].sudo().set_str('predict_late_payment.gemini_api_key', '')
        result = self.ai_service.analyze_customer(self.partner, self.dummy_stats)
        self.assertFalse(result.get('ai_powered'))
        self.assertIn('statistical rules', result.get('ai_reasoning'))

    @patch('odoo.addons.predict_late_payment.models.ai_service.PaymentRiskAIService._call_gemini')
    def test_analyze_customer_with_api_key_success(self, mock_call):
        """Test analyze_customer parses successful Gemini AI response."""
        self.env['ir.config_parameter'].sudo().set_str(
            'predict_late_payment.gemini_api_key', 'AIzaSyTestMockKey'
        )
        mock_response = json.dumps({
            'score': 22.0,
            'risk_level': 'low',
            'delay_score': 4.0,
            'overdue_score': 0.0,
            'consistency_score': 3.0,
            'recency_score': 2.0,
            'volume_score': 5.0,
            'trend_score': -1.0,
            'suggested_credit_limit': 8000.0,
            'ai_reasoning': 'Customer pays promptly with minimal delays.',
            'followup_suggestion': 'Standard payment terms apply.',
            'followup_email': 'Thank you for your business.',
        })
        mock_call.return_value = mock_response

        res = self.ai_service.analyze_customer(self.partner, self.dummy_stats)
        self.assertTrue(res['ai_powered'])
        self.assertEqual(res['score'], 22.0)
        self.assertIn('Google Gemini', res['ai_backend'])

    @patch('odoo.addons.predict_late_payment.models.ai_service.PaymentRiskAIService._call_gemini')
    def test_analyze_customer_http_errors(self, mock_call):
        """Test analyze_customer handles various HTTP error codes gracefully."""
        self.env['ir.config_parameter'].sudo().set_str(
            'predict_late_payment.gemini_api_key', 'AIzaSyTestMockKey'
        )

        for code in (429, 401, 400, 500):
            mock_call.side_effect = urllib.error.HTTPError(
                'https://api.test', code, 'Test Error', {}, io.BytesIO(b'Error message')
            )
            res = self.ai_service.analyze_customer(self.partner, self.dummy_stats)
            self.assertFalse(res['ai_powered'])
            self.assertIn('fallback', res['ai_reasoning'].lower())

    @patch('odoo.addons.predict_late_payment.models.ai_service.PaymentRiskAIService._call_gemini')
    def test_analyze_customer_generic_exception(self, mock_call):
        """Test analyze_customer handles generic exception."""
        self.env['ir.config_parameter'].sudo().set_str(
            'predict_late_payment.gemini_api_key', 'AIzaSyTestMockKey'
        )
        mock_call.side_effect = Exception("Connection timed out")
        res = self.ai_service.analyze_customer(self.partner, self.dummy_stats)
        self.assertFalse(res['ai_powered'])
        self.assertIn('Statistical fallback used', res['ai_reasoning'])

    def test_test_connection_no_key(self):
        """Test test_connection returns warning when key is missing."""
        self.env['ir.config_parameter'].sudo().set_str('predict_late_payment.gemini_api_key', '')
        msg = self.ai_service.test_connection()
        self.assertIn('No API key configured', msg)

    @patch('odoo.addons.predict_late_payment.models.ai_service.PaymentRiskAIService._call_gemini')
    def test_test_connection_success(self, mock_call):
        """Test test_connection returns OK on successful connection."""
        self.env['ir.config_parameter'].sudo().set_str(
            'predict_late_payment.gemini_api_key', 'AIzaSyTestMockKey'
        )
        mock_call.return_value = 'CONNECTED'
        msg = self.ai_service.test_connection()
        self.assertTrue(msg.startswith('OK'))

    @patch('odoo.addons.predict_late_payment.models.ai_service.PaymentRiskAIService._call_gemini')
    def test_test_connection_errors(self, mock_call):
        """Test test_connection handles HTTPError and URLError."""
        self.env['ir.config_parameter'].sudo().set_str(
            'predict_late_payment.gemini_api_key', 'AIzaSyTestMockKey'
        )
        mock_call.side_effect = urllib.error.HTTPError(
            'https://api.test', 403, 'Forbidden', {}, io.BytesIO(b'Invalid API Key')
        )
        msg = self.ai_service.test_connection()
        self.assertIn('HTTP 403', msg)

        mock_call.side_effect = urllib.error.URLError('Name or service not known')
        msg2 = self.ai_service.test_connection()
        self.assertIn('Network error', msg2)
