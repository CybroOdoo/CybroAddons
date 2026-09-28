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
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestAccountMove(common.TransactionCase):
    """Test suite for models/account_move.py methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner AccountMove',
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

    def test_compute_anomaly_alert_count(self):
        """Test _compute_anomaly_alert_count method."""
        self.assertEqual(self.move.anomaly_alert_count, 0)

        # Create active alert
        alert1 = self.env['account.anomaly.alert'].create({
            'title': 'Alert 1',
            'description': 'Description 1',
            'alert_type': 'amount_outlier',
            'anomaly_score': 70,
            'risk_level': 'high',
            'move_id': self.move.id,
            'company_id': self.company.id,
            'state': 'open',
        })
        self.move._compute_anomaly_alert_count()
        self.assertEqual(self.move.anomaly_alert_count, 1)

        # Create resolved alert
        alert2 = self.env['account.anomaly.alert'].create({
            'title': 'Alert 2',
            'description': 'Description 2',
            'alert_type': 'round_number',
            'anomaly_score': 20,
            'risk_level': 'low',
            'move_id': self.move.id,
            'company_id': self.company.id,
            'state': 'resolved',
            'resolution_note': 'Resolved',
        })
        self.move._compute_anomaly_alert_count()
        self.assertEqual(self.move.anomaly_alert_count, 1)

        # Create false positive alert
        alert3 = self.env['account.anomaly.alert'].create({
            'title': 'Alert 3',
            'description': 'Description 3',
            'alert_type': 'unusual_timing',
            'anomaly_score': 40,
            'risk_level': 'medium',
            'move_id': self.move.id,
            'company_id': self.company.id,
            'state': 'false_positive',
        })
        self.move._compute_anomaly_alert_count()
        self.assertEqual(self.move.anomaly_alert_count, 1)

    def test_compute_anomaly_risk_level(self):
        """Test _compute_anomaly_risk_level method."""
        self.move._compute_anomaly_risk_level()
        self.assertEqual(self.move.anomaly_risk_level, 'clean')

        # Add medium risk alert
        alert_medium = self.env['account.anomaly.alert'].create({
            'title': 'Medium Alert',
            'description': 'Desc',
            'alert_type': 'round_number',
            'anomaly_score': 50,
            'risk_level': 'medium',
            'move_id': self.move.id,
            'company_id': self.company.id,
            'state': 'open',
        })
        self.move._compute_anomaly_risk_level()
        self.assertEqual(self.move.anomaly_risk_level, 'medium')

        # Add critical risk alert
        alert_critical = self.env['account.anomaly.alert'].create({
            'title': 'Critical Alert',
            'description': 'Desc',
            'alert_type': 'amount_outlier',
            'anomaly_score': 95,
            'risk_level': 'critical',
            'move_id': self.move.id,
            'company_id': self.company.id,
            'state': 'open',
        })
        self.move._compute_anomaly_risk_level()
        self.assertEqual(self.move.anomaly_risk_level, 'critical')

    def test_action_post(self):
        """Test action_post method triggers scan when configured."""
        self.company.anomaly_scan_on_post = True
        account_debit = self.env['account.account'].search([
            ('company_ids', 'in', [self.company.id]),
            ('account_type', '=', 'expense')
        ], limit=1)
        account_credit = self.env['account.account'].search([
            ('company_ids', 'in', [self.company.id]),
            ('account_type', '=', 'asset_cash')
        ], limit=1)

        if account_debit and account_credit:
            test_move = self.env['account.move'].create({
                'move_type': 'entry',
                'journal_id': self.journal.id,
                'line_ids': [
                    (0, 0, {'account_id': account_debit.id, 'debit': 1000.0, 'credit': 0.0}),
                    (0, 0, {'account_id': account_credit.id, 'debit': 0.0, 'credit': 1000.0}),
                ]
            })
            test_move.action_post()
            self.assertEqual(test_move.state, 'posted')

    def test_action_view_anomaly_alerts(self):
        """Test action_view_anomaly_alerts method returns correct action."""
        action = self.move.action_view_anomaly_alerts()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'account.anomaly.alert')
        self.assertEqual(action['domain'], [('move_id', '=', self.move.id)])
