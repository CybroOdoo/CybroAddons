# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1). It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included in
#    all copies or substantial portions of the Software.
#
#############################################################################

import json
from unittest.mock import patch, MagicMock
import requests
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError


class TestHelpdeskTicket(TransactionCase):

    def setUp(self):
        super(TestHelpdeskTicket, self).setUp()
        self.Ticket = self.env['helpdesk.ticket']
        self.Partner = self.env['res.partner']
        self.User = self.env['res.users']

        # Setup standard config parameters
        self.env['ir.config_parameter'].sudo().set_param(
            'customer_success_sentiment_tracker.openai_api_key', 'test_key'
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'customer_success_sentiment_tracker.enable_ai', 'True'
        )

        # Create dummy customer and internal user
        self.customer = self.Partner.create({
            'name': 'Test Customer',
            'email': 'customer@example.com',
        })

        # Internal user setup
        self.internal_partner = self.Partner.create({
            'name': 'Internal User Partner',
            'email': 'internal@example.com',
        })
        self.internal_user = self.User.create({
            'name': 'Internal User',
            'login': 'internal_user_login',
            'partner_id': self.internal_partner.id,
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('helpdesk.group_helpdesk_user').id
            ])],
        })

    def test_compute_sentiment_percent_and_human(self):
        """Test the compute methods for sentiment_percent and sentiment_human."""
        # Case 1: sentiment_score is False
        ticket = self.Ticket.create({'name': 'Test Ticket 1', 'sentiment_score': False})
        self.assertEqual(ticket.sentiment_percent, 50)
        self.assertEqual(ticket.sentiment_human, 'Neutral 🟡')

        # Case 2: Very Frustrated
        ticket.write({'sentiment_score': -0.7})
        self.assertEqual(ticket.sentiment_percent, 15)
        self.assertEqual(ticket.sentiment_human, 'Very Frustrated 🔴')

        # Case 3: Unhappy
        ticket.write({'sentiment_score': -0.3})
        self.assertEqual(ticket.sentiment_percent, 35)
        self.assertEqual(ticket.sentiment_human, 'Unhappy 🟠')

        # Case 4: Neutral
        ticket.write({'sentiment_score': 0.1})
        self.assertEqual(ticket.sentiment_percent, 55)
        self.assertEqual(ticket.sentiment_human, 'Neutral 🟡')

        # Case 5: Satisfied
        ticket.write({'sentiment_score': 0.5})
        self.assertEqual(ticket.sentiment_percent, 75)
        self.assertEqual(ticket.sentiment_human, 'Satisfied 🟢')

        # Case 6: Very Happy
        ticket.write({'sentiment_score': 0.9})
        self.assertEqual(ticket.sentiment_percent, 95)
        self.assertEqual(ticket.sentiment_human, 'Very Happy 🟢')

    @patch('requests.post')
    def test_ticket_creation_sentiment_analysis(self, mock_post):
        """Test that sentiment analysis is triggered on ticket creation for external customers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"score": -0.8}'
                }
            }]
        }
        mock_post.return_value = mock_response

        # Create ticket with customer and description
        ticket = self.Ticket.create({
            'name': 'Angry Customer Ticket',
            'partner_id': self.customer.id,
            'description': 'I am extremely unhappy with the product!',
        })

        # Verify mock post was called
        self.assertTrue(mock_post.called)
        self.assertEqual(ticket.sentiment_score, -0.8)
        self.assertEqual(ticket.risk_level, 'high')
        self.assertTrue(ticket.is_high_risk)

    @patch('requests.post')
    def test_ticket_creation_by_internal_user(self, mock_post):
        """Test that sentiment analysis is not triggered for internal users."""
        ticket = self.Ticket.with_user(self.internal_user).create({
            'name': 'Internal Ticket',
            'partner_id': self.internal_partner.id,
            'description': 'Internal user ticket description',
        })
        self.assertFalse(mock_post.called)
        self.assertFalse(ticket.sentiment_score)

    @patch('requests.post')
    def test_message_post_sentiment_analysis(self, mock_post):
        """Test that sentiment analysis is triggered when an external customer replies via message_post."""
        ticket = self.Ticket.create({'name': 'Discussion Ticket'})
        mock_post.reset_mock()

        # Mock API response for positive sentiment
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"score": 0.7}'
                }
            }]
        }
        mock_post.return_value = mock_response

        # Post comment as customer
        ticket.message_post(
            body='Thank you, this works perfectly!',
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            author_id=self.customer.id
        )

        self.assertTrue(mock_post.called)
        self.assertEqual(ticket.sentiment_score, 0.7)
        self.assertEqual(ticket.risk_level, 'low')
        self.assertFalse(ticket.is_high_risk)

    @patch('requests.post')
    def test_message_post_internal_or_wrong_type(self, mock_post):
        """Test that sentiment analysis is not triggered for internal notes or wrong message types."""
        ticket = self.Ticket.create({'name': 'Discussion Ticket'})

        # Case 1: Internal note (subtype is internal)
        internal_subtype = self.env.ref('mail.mt_note')
        ticket.message_post(
            body='Internal notes discussion',
            message_type='comment',
            subtype_id=internal_subtype.id
        )
        self.assertFalse(mock_post.called)

        # Case 2: Notification message type (not comment or email)
        ticket.message_post(
            body='System notification',
            message_type='notification'
        )
        self.assertFalse(mock_post.called)

    @patch('requests.post')
    def test_create_high_risk_activity(self, mock_post):
        """Test that a high risk activity is created for helpdesk managers when sentiment is high risk."""
        # Ensure we have a helpdesk manager user/group
        manager_group = self.env.ref('helpdesk.group_helpdesk_manager')
        manager = self.User.create({
            'name': 'Helpdesk Manager',
            'login': 'manager_user_login_test',
            'group_ids': [(6, 0, [manager_group.id])],
        })

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '{"score": -0.9}'
                }
            }]
        }
        mock_post.return_value = mock_response

        ticket = self.Ticket.create({
            'name': 'Critical Issue',
            'partner_id': self.customer.id,
            'description': 'System is down!',
        })

        # Check that high-risk activity has been scheduled for the manager
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'helpdesk.ticket'),
            ('res_id', '=', ticket.id),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('user_id', '=', manager.id)
        ])
        self.assertTrue(activities)
