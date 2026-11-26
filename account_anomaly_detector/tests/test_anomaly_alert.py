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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError


@tagged('post_install', '-at_install')
class TestAccountAnomalyAlert(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.user = cls.env.user

        cls.partner = cls.env['res.partner'].create({
            'name': 'Alert Test Partner',
        })

        cls.account = cls.env['account.account'].search([
            ('company_id', '=', cls.company.id)
        ], limit=1)

        cls.move = cls.env['account.move'].create({
            'company_id': cls.company.id,
            'partner_id': cls.partner.id,
            'move_type': 'entry',
            'line_ids': [
                (0, 0, {'name': 'D', 'account_id': cls.account.id, 'debit': 500.0}),
                (0, 0, {'name': 'C', 'account_id': cls.account.id, 'credit': 500.0}),
            ]
        })

        cls.alert = cls.env['account.anomaly.alert'].create({
            'title': 'Test Anomaly Alert',
            'description': 'Anomaly detection test description.',
            'alert_type': 'amount_outlier',
            'risk_level': 'medium',
            'anomaly_score': 50,
            'move_id': cls.move.id,
            'company_id': cls.company.id,
        })

    def test_01_computed_risk_level_and_colors(self):
        """Test risk level computation according to score ranges."""
        alert = self.alert

        alert.anomaly_score = 20
        alert._compute_risk_level()
        self.assertEqual(alert.risk_level, 'low')
        self.assertEqual(alert.risk_color, 4)

        alert.anomaly_score = 50
        alert._compute_risk_level()
        self.assertEqual(alert.risk_level, 'medium')
        self.assertEqual(alert.risk_color, 3)

        alert.anomaly_score = 75
        alert._compute_risk_level()
        self.assertEqual(alert.risk_level, 'high')
        self.assertEqual(alert.risk_color, 2)

        alert.anomaly_score = 95
        alert._compute_risk_level()
        self.assertEqual(alert.risk_level, 'critical')
        self.assertEqual(alert.risk_color, 1)

    def test_02_type_icon_and_days_open(self):
        """Test emoji type icons and days open calculation."""
        alert = self.alert
        alert.alert_type = 'amount_outlier'
        alert._compute_type_icon()
        self.assertEqual(alert.alert_type_icon, '📊')

        alert.alert_type = 'duplicate_vendor_bill'
        alert._compute_type_icon()
        self.assertEqual(alert.alert_type_icon, '📋')

        alert._compute_days_open()
        self.assertGreaterEqual(alert.days_open, 0)

    def test_03_lifecycle_workflow_actions(self):
        """Test alert state transition methods."""
        alert = self.alert
        self.assertEqual(alert.state, 'open')

        # Investigate
        alert.action_investigate()
        self.assertEqual(alert.state, 'investigating')
        self.assertEqual(alert.assigned_to.id, self.env.user.id)

        # Escalate
        alert.action_escalate()
        self.assertEqual(alert.state, 'escalated')

        # Resolve without resolution notes raises UserError
        with self.assertRaises(UserError):
            alert.action_resolve()

        # Resolve with resolution note succeeds
        alert.resolution_note = 'Verified supporting invoice.'
        alert.action_resolve()
        self.assertEqual(alert.state, 'resolved')
        self.assertTrue(alert.resolved_date)
        self.assertEqual(alert.reviewed_by.id, self.env.user.id)

        # Mark False Positive
        alert2 = self.env['account.anomaly.alert'].create({
            'title': 'Test FP Alert',
            'description': 'False positive test',
            'alert_type': 'round_number',
            'anomaly_score': 30,
            'move_id': self.move.id,
            'company_id': self.company.id,
        })
        alert2.action_mark_false_positive()
        self.assertEqual(alert2.state, 'false_positive')

    def test_04_assign_to_me_and_view_journal_entry(self):
        """Test assignment and journal entry view action."""
        alert = self.alert
        alert.action_assign_to_me()
        self.assertEqual(alert.assigned_to.id, self.env.user.id)

        action = alert.action_view_journal_entry()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_id'], self.move.id)

        # Alert without move raises UserError
        alert_no_move = self.env['account.anomaly.alert'].create({
            'title': 'No Move Alert',
            'description': 'No move',
            'alert_type': 'manual',
            'anomaly_score': 10,
            'company_id': self.company.id,
        })
        with self.assertRaises(UserError):
            alert_no_move.action_view_journal_entry()

    def test_05_batch_actions(self):
        """Test bulk resolution and false positive actions."""
        a1 = self.env['account.anomaly.alert'].create({
            'title': 'Batch 1', 'description': 'desc', 'alert_type': 'manual',
            'company_id': self.company.id,
        })
        a2 = self.env['account.anomaly.alert'].create({
            'title': 'Batch 2', 'description': 'desc', 'alert_type': 'manual',
            'company_id': self.company.id,
        })
        batch = a1 | a2
        batch.action_batch_resolve()
        self.assertEqual(a1.state, 'resolved')
        self.assertEqual(a2.state, 'resolved')

        a3 = self.env['account.anomaly.alert'].create({
            'title': 'Batch 3', 'description': 'desc', 'alert_type': 'manual',
            'company_id': self.company.id,
        })
        a3.action_batch_false_positive()
        self.assertEqual(a3.state, 'false_positive')

    def test_06_score_constrains(self):
        """Test score validation constrains."""
        with self.assertRaises(ValidationError):
            self.env['account.anomaly.alert'].create({
                'title': 'Invalid Score',
                'description': 'Test invalid score',
                'alert_type': 'manual',
                'anomaly_score': 150,
                'company_id': self.company.id,
            })
