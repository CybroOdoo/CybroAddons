# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from datetime import timedelta
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSentimentTracker(TransactionCase):
    """Test suite for Customer Success Sentiment Tracker module."""

    @classmethod
    def setUpClass(cls):
        """Set up test data: customer, team, stages, and config."""
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Sentiment Test Customer',
            'email': 'customer@example.com',
        })
        cls.team = cls.env['helpdesk.team'].create({
            'name': 'Test Support Team',
        })
        cls.stage_progress = cls.env['helpdesk.stage'].create({
            'name': 'In Progress',
            'team_ids': [(4, cls.team.id)],
            'fold': False,
        })
        cls.stage_closed = cls.env['helpdesk.stage'].create({
            'name': 'Resolved',
            'team_ids': [(4, cls.team.id)],
            'fold': True,
        })
        cls.config_param = cls.env['ir.config_parameter'].sudo()

    def test_01_sentiment_percent_and_human(self):
        """Verify sentiment_percent and sentiment_human computations."""
        ticket = self.env['helpdesk.ticket'].create({
            'name': 'Mood Test Ticket',
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'sentiment_score': -0.8,
        })
        self.assertEqual(ticket.sentiment_percent, 10)
        self.assertEqual(ticket.sentiment_human, "Very Frustrated 🔴")

        ticket.sentiment_score = -0.4
        self.assertEqual(ticket.sentiment_percent, 30)
        self.assertEqual(ticket.sentiment_human, "Unhappy 🟠")

        ticket.sentiment_score = 0.0
        self.assertEqual(ticket.sentiment_percent, 50)
        self.assertEqual(ticket.sentiment_human, "Neutral 🟡")

        ticket.sentiment_score = 0.5
        self.assertEqual(ticket.sentiment_percent, 75)
        self.assertEqual(ticket.sentiment_human, "Satisfied 🟢")

        ticket.sentiment_score = 0.9
        self.assertEqual(ticket.sentiment_percent, 95)
        self.assertEqual(ticket.sentiment_human, "Very Happy 🟢")

    def test_02_extract_json(self):
        """Test JSON extraction logic from raw responses."""
        ticket = self.env['helpdesk.ticket'].new({'name': 'Dummy Ticket'})
        valid_raw = 'Here is the score: {"score": 0.75} Hope this helps!'
        extracted = ticket._extract_json(valid_raw)
        self.assertEqual(extracted, {"score": 0.75})

        invalid_raw = 'No json block here'
        self.assertIsNone(ticket._extract_json(invalid_raw))

        corrupt_raw = '{"score": invalid_json}'
        self.assertIsNone(ticket._extract_json(corrupt_raw))

    def test_03_run_sentiment_analysis_mocked(self):
        """Test AI sentiment analysis response processing and risk activity."""
        self.config_param.set_str(
            'customer_success_sentiment_tracker.openai_api_key', 'test_key'
        )
        ticket = self.env['helpdesk.ticket'].create({
            'name': 'AI Analysis Ticket',
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': '<p>I am extremely furious with the service!</p>',
        })

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"score": -0.85}'
                }
            }]
        }

        with patch('requests.post', return_value=mock_resp):
            ticket.action_analyze_sentiment()

        self.assertEqual(ticket.sentiment_score, -0.85)
        self.assertEqual(ticket.risk_level, 'high')
        self.assertTrue(ticket.is_high_risk)

        # Check positive sentiment
        mock_resp.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"score": 0.9}'
                }
            }]
        }
        with patch('requests.post', return_value=mock_resp):
            ticket._run_sentiment_analysis('Thank you, wonderful help!')

        self.assertEqual(ticket.sentiment_score, 0.9)
        self.assertEqual(ticket.risk_level, 'low')
        self.assertFalse(ticket.is_high_risk)

    def test_04_default_customer_health(self):
        """Customer with no tickets defaults to maximum health score (100)."""
        new_partner = self.env['res.partner'].create({
            'name': 'Clean Customer',
        })
        new_partner._compute_customer_health()
        self.assertEqual(new_partner.customer_health_score, 100)
        self.assertEqual(new_partner.customer_health_label, "Healthy 🟢")
        self.assertFalse(new_partner.is_at_risk)

    def test_05_90_day_sentiment_decay_and_recovery(self):
        """Verify time-weighted 90-day decay and score recovery."""
        now = fields.Datetime.now()
        # Older ticket created 75 days ago with negative score
        t1 = self.env['helpdesk.ticket'].create({
            'name': 'Old Critical Ticket',
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'stage_id': self.stage_progress.id,
            'sentiment_score': -0.8,
        })
        t1.write({'create_date': now - timedelta(days=75)})

        self.partner._compute_customer_health()
        score_before_recovery = self.partner.customer_health_score

        # Recent ticket created today with positive score
        t2 = self.env['helpdesk.ticket'].create({
            'name': 'Recent Happy Ticket',
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'stage_id': self.stage_progress.id,
            'sentiment_score': 0.8,
        })
        t2.write({'create_date': now})

        self.partner._compute_customer_health()
        score_after_recovery = self.partner.customer_health_score

        # Recent positive interaction dominates the decayed old interaction
        self.assertGreater(score_after_recovery, score_before_recovery)

    def test_06_closed_ticket_halved_negative_score(self):
        """Verify that resolved negative tickets have reduced penalty."""
        now = fields.Datetime.now()
        ticket = self.env['helpdesk.ticket'].create({
            'name': 'Ticket Under Review',
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'stage_id': self.stage_progress.id,
            'sentiment_score': -0.8,
        })
        ticket.write({'create_date': now})
        self.partner._compute_customer_health()
        open_health = self.partner.customer_health_score

        # Close the ticket
        ticket.stage_id = self.stage_closed.id
        self.partner._compute_customer_health()
        closed_health = self.partner.customer_health_score

        # Closed negative score is halved (-0.4 instead of -0.8),
        # improving health
        self.assertGreater(closed_health, open_health)

    def test_07_cron_recompute_customer_health(self):
        """Test automated daily cron recomputation and ir.cron existence."""
        cron = self.env.ref(
            'customer_success_sentiment_tracker.'
            'ir_cron_recompute_customer_health',
            raise_if_not_found=False
        )
        self.assertIsNotNone(cron)
        self.assertEqual(cron.interval_type, 'days')

        # Execute the cron method directly
        self.env['res.partner']._cron_recompute_customer_health()
        self.assertTrue(self.partner.customer_health_score >= 0)

    def test_08_res_config_settings_validation(self):
        """Test configuration validation and connection checks."""
        settings = self.env['res.config.settings'].new({
            'enable_ai_sentiment': True,
            'openai_api_key': False,
        })
        with self.assertRaises(ValidationError):
            settings.set_values()

        with self.assertRaises(ValidationError):
            settings.action_test_openai_connection()

        # Test valid connection mock
        settings.openai_api_key = 'sk-valid-key'
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch('requests.get', return_value=mock_resp):
            action = settings.action_test_openai_connection()
            self.assertEqual(action.get('type'), 'ir.actions.client')
            self.assertEqual(action.get('params', {}).get('type'), 'success')
