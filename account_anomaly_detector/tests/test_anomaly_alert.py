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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields
from odoo.tests import common, tagged
from odoo.exceptions import UserError
from datetime import timedelta


@tagged('post_install', '-at_install')
class TestAnomalyAlert(common.TransactionCase):
    """Test suite for models/anomaly_alert.py methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner AnomalyAlert',
        })
        cls.journal = cls.env['account.journal'].search([
            ('company_id', '=', cls.company.id),
            ('type', '=', 'general')
        ], limit=1)

        cls.move = cls.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': cls.journal.id,
            'partner_id': cls.partner.id,
        })

        cls.alert = cls.env['account.anomaly.alert'].create({
            'title': 'Test Anomaly Alert',
            'description': 'Test anomaly alert description',
            'alert_type': 'amount_outlier',
            'anomaly_score': 75,
            'risk_level': 'high',
            'move_id': cls.move.id,
            'company_id': cls.company.id,
        })

    def test_compute_risk_level(self):
        """Test _compute_risk_level method across score boundaries."""
        alert = self.alert
        alert.anomaly_score = 20
        alert._compute_risk_level()
        self.assertEqual(alert.risk_level, 'low')

        alert.anomaly_score = 50
        alert._compute_risk_level()
        self.assertEqual(alert.risk_level, 'medium')

        alert.anomaly_score = 80
        alert._compute_risk_level()
        self.assertEqual(alert.risk_level, 'high')

        alert.anomaly_score = 95
        alert._compute_risk_level()
        self.assertEqual(alert.risk_level, 'critical')

    def test_compute_risk_color(self):
        """Test _compute_risk_color method."""
        alert = self.alert
        alert.risk_level = 'critical'
        alert._compute_risk_color()
        self.assertEqual(alert.risk_color, 1)

        alert.risk_level = 'high'
        alert._compute_risk_color()
        self.assertEqual(alert.risk_color, 2)

        alert.risk_level = 'medium'
        alert._compute_risk_color()
        self.assertEqual(alert.risk_color, 3)

        alert.risk_level = 'low'
        alert._compute_risk_color()
        self.assertEqual(alert.risk_color, 4)

    def test_compute_type_icon(self):
        """Test _compute_type_icon method."""
        types_and_icons = [
            ('amount_outlier', '📊'),
            ('duplicate_vendor_bill', '📋'),
            ('round_number', '🔢'),
            ('velocity_spike', '⚡'),
            ('unusual_timing', '🕐'),
            ('spending_deviation', '📈'),
            ('benfords_violation', '🔬'),
            ('unusual_account_combo', '⚠️'),
            ('vendor_concentration', '🏢'),
            ('manual', '✏️'),
        ]
        for alert_type, icon in types_and_icons:
            self.alert.alert_type = alert_type
            self.alert._compute_type_icon()
            self.assertEqual(self.alert.alert_type_icon, icon)

    def test_compute_days_open(self):
        """Test _compute_days_open method."""
        self.alert.detected_date = fields.Datetime.now() - timedelta(days=5, hours=1)
        self.alert.state = 'open'
        self.alert._compute_days_open()
        self.assertEqual(self.alert.days_open, 5)

        self.alert.state = 'resolved'
        self.alert._compute_days_open()
        self.assertEqual(self.alert.days_open, 0)

    def test_action_investigate(self):
        """Test action_investigate method."""
        self.alert.action_investigate()
        self.assertEqual(self.alert.state, 'investigating')
        self.assertEqual(self.alert.assigned_to, self.env.user)

    def test_action_resolve(self):
        """Test action_resolve method validation and state update."""
        self.alert.resolution_note = False
        with self.assertRaises(UserError):
            self.alert.action_resolve()

        self.alert.resolution_note = 'Verified with management'
        self.alert.action_resolve()
        self.assertEqual(self.alert.state, 'resolved')
        self.assertTrue(self.alert.resolved_date)
        self.assertEqual(self.alert.reviewed_by, self.env.user)

    def test_action_mark_false_positive(self):
        """Test action_mark_false_positive method."""
        self.alert.action_mark_false_positive()
        self.assertEqual(self.alert.state, 'false_positive')
        self.assertTrue(self.alert.resolved_date)
        self.assertEqual(self.alert.reviewed_by, self.env.user)

    def test_action_escalate(self):
        """Test action_escalate method."""
        self.alert.action_escalate()
        self.assertEqual(self.alert.state, 'escalated')

    def test_action_view_journal_entry(self):
        """Test action_view_journal_entry method."""
        action = self.alert.action_view_journal_entry()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'account.move')
        self.assertEqual(action['res_id'], self.move.id)

        # Test without move_id
        alert_no_move = self.env['account.anomaly.alert'].create({
            'title': 'No Move Alert',
            'description': 'Desc',
            'alert_type': 'manual',
            'anomaly_score': 50,
            'risk_level': 'medium',
            'company_id': self.company.id,
        })
        with self.assertRaises(UserError):
            alert_no_move.action_view_journal_entry()

    def test_action_assign_to_me(self):
        """Test action_assign_to_me method."""
        self.alert.action_assign_to_me()
        self.assertEqual(self.alert.assigned_to, self.env.user)

    def test_action_batch_resolve(self):
        """Test action_batch_resolve method."""
        alert2 = self.env['account.anomaly.alert'].create({
            'title': 'Batch Alert 2',
            'description': 'Desc',
            'alert_type': 'round_number',
            'anomaly_score': 30,
            'risk_level': 'low',
            'company_id': self.company.id,
        })
        alerts = self.alert | alert2
        alerts.action_batch_resolve()
        self.assertEqual(self.alert.state, 'resolved')
        self.assertEqual(alert2.state, 'resolved')

    def test_action_batch_false_positive(self):
        """Test action_batch_false_positive method."""
        alert2 = self.env['account.anomaly.alert'].create({
            'title': 'Batch FP Alert 2',
            'description': 'Desc',
            'alert_type': 'round_number',
            'anomaly_score': 30,
            'risk_level': 'low',
            'company_id': self.company.id,
        })
        alerts = self.alert | alert2
        alerts.action_batch_false_positive()
        self.assertEqual(self.alert.state, 'false_positive')
        self.assertEqual(alert2.state, 'false_positive')

    def test_check_anomaly_score_constraint(self):
        """Test _check_anomaly_score constraint validation."""
        with self.assertRaises(UserError):
            self.env['account.anomaly.alert'].create({
                'title': 'Invalid Score Alert',
                'description': 'Desc',
                'alert_type': 'manual',
                'anomaly_score': 150,
                'risk_level': 'critical',
                'company_id': self.company.id,
            })
