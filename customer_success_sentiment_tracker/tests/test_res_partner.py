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

from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo import fields


class TestResPartner(TransactionCase):

    def setUp(self):
        super(TestResPartner, self).setUp()
        self.Partner = self.env['res.partner']
        self.Ticket = self.env['helpdesk.ticket']
        self.Stage = self.env['helpdesk.stage']

        # Create partner
        self.partner = self.Partner.create({
            'name': 'Health Test Partner',
            'email': 'health@example.com',
        })

        # Create a team
        self.team = self.env['helpdesk.team'].create({
            'name': 'Test Support Team',
        })

        # Create open and closed ticket stages
        self.open_stage = self.Stage.create({
            'name': 'New',
            'fold': False,
            'team_ids': [(4, self.team.id)],
        })
        self.closed_stage = self.Stage.create({
            'name': 'Closed',
            'fold': True,
            'team_ids': [(4, self.team.id)],
        })

    def test_partner_health_no_tickets(self):
        """Test health score for a partner with no tickets."""
        # Triggers compute
        self.partner._compute_customer_health()
        self.assertEqual(self.partner.customer_health_score, 100)
        self.assertEqual(self.partner.customer_health_label, 'Healthy 🟢')
        self.assertFalse(self.partner.is_at_risk)

    def test_partner_health_single_positive_ticket(self):
        """Test health score for a partner with a single positive ticket."""
        self.Ticket.create({
            'name': 'Positive Ticket',
            'partner_id': self.partner.id,
            'sentiment_score': 0.5,
            'stage_id': self.open_stage.id,
            'create_date': fields.Datetime.now() - timedelta(days=10),
        })

        self.partner._compute_customer_health()
        # sentiment_pts = int((0.5 + 1) * 30) = 45
        # volume_pts = 15 (1 ticket in last 30d)
        # critical_pts = 20 (0 critical tickets in last 60d)
        # final_score = 45 + 15 + 20 = 80
        self.assertEqual(self.partner.customer_health_score, 80)
        self.assertEqual(self.partner.customer_health_label, 'Healthy 🟢')
        self.assertFalse(self.partner.is_at_risk)

    def test_partner_health_multiple_negative_tickets(self):
        """Test health score for a partner with multiple negative tickets."""
        # Ticket 1: 5 days ago, sentiment_score = -0.8 (Critical)
        self.Ticket.create({
            'name': 'Very Angry Ticket',
            'partner_id': self.partner.id,
            'sentiment_score': -0.8,
            'stage_id': self.open_stage.id,
            'create_date': fields.Datetime.now() - timedelta(days=5),
        })
        # Ticket 2: 15 days ago, sentiment_score = -0.4
        self.Ticket.create({
            'name': 'Unhappy Ticket',
            'partner_id': self.partner.id,
            'sentiment_score': -0.4,
            'stage_id': self.open_stage.id,
            'create_date': fields.Datetime.now() - timedelta(days=15),
        })

        self.partner._compute_customer_health()
        # avg_score = (-0.8 + -0.4) / 2 = -0.6
        # sentiment_pts = int((-0.6 + 1) * 30) = int(11.99999...) = 11 (due to float precision)
        # volume_pts = 15 (2 tickets in last 30d)
        # critical_pts = 10 (1 critical ticket in last 60d)
        # final_score = 11 + 15 + 10 = 36
        self.assertEqual(self.partner.customer_health_score, 36)
        self.assertEqual(self.partner.customer_health_label, 'Attention Needed 🟠')
        self.assertFalse(self.partner.is_at_risk)

    def test_partner_health_critical_risk(self):
        """Test health score for a partner in Critical Risk state."""
        # 5 critical tickets in the last 10 days
        for i in range(5):
            self.Ticket.create({
                'name': f'Critical Ticket {i}',
                'partner_id': self.partner.id,
                'sentiment_score': -0.8,
                'stage_id': self.open_stage.id,
                'create_date': fields.Datetime.now() - timedelta(days=2),
            })

        self.partner._compute_customer_health()
        # avg_score = -0.8
        # sentiment_pts = int((-0.8 + 1) * 30) = int(5.99999...) = 5 (due to float precision)
        # volume_pts = 0 (>= 5 tickets in last 30d)
        # critical_pts = 0 (>= 2 critical tickets in last 60d)
        # final_score = 5 + 0 + 0 = 5
        self.assertEqual(self.partner.customer_health_score, 5)
        self.assertEqual(self.partner.customer_health_label, 'Critical Risk 🔴')
        self.assertTrue(self.partner.is_at_risk)

    def test_partner_health_closed_ticket_sentiment_halved(self):
        """Test that closed negative tickets have their sentiment score halved in the calculation."""
        # Create a closed ticket with sentiment -0.8 (Normally critical, but will be halved to -0.4)
        self.Ticket.create({
            'name': 'Closed Ticket',
            'partner_id': self.partner.id,
            'sentiment_score': -0.8,
            'stage_id': self.closed_stage.id,
            'create_date': fields.Datetime.now() - timedelta(days=10),
        })

        self.partner._compute_customer_health()
        # Since closed and score < 0, score = -0.8 / 2 = -0.4
        # avg_score = -0.4
        # sentiment_pts = int((-0.4 + 1) * 30) = 18
        # volume_pts = 15 (1 ticket in last 30d)
        # critical_pts = 20 (score was halved to -0.4, which is > -0.6, so 0 critical tickets in last 60d)
        # final_score = 18 + 15 + 20 = 53
        self.assertEqual(self.partner.customer_health_score, 53)
        self.assertEqual(self.partner.customer_health_label, 'Attention Needed 🟠')
        self.assertFalse(self.partner.is_at_risk)
