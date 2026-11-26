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


@tagged('post_install', '-at_install')
class TestAccountMoveAnomaly(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner Account Move',
        })

        # Find or create a test journal
        cls.journal = cls.env['account.journal'].search([
            ('company_id', '=', cls.company.id),
            ('type', '=', 'general')
        ], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Miscellaneous Test Journal',
                'code': 'MISCT',
                'type': 'general',
                'company_id': cls.company.id,
            })

        # Create a test account
        cls.account = cls.env['account.account'].search([
            ('company_id', '=', cls.company.id)
        ], limit=1)

        # Create a journal entry
        cls.move = cls.env['account.move'].create({
            'journal_id': cls.journal.id,
            'partner_id': cls.partner.id,
            'move_type': 'entry',
            'line_ids': [
                (0, 0, {
                    'name': 'Debit Line',
                    'account_id': cls.account.id,
                    'debit': 1000.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': 'Credit Line',
                    'account_id': cls.account.id,
                    'debit': 0.0,
                    'credit': 1000.0,
                }),
            ]
        })

    def test_01_anomaly_alert_count_and_risk_level_computation(self):
        """Test calculation of alert counts and worst severity risk level on move."""
        self.assertEqual(self.move.anomaly_risk_level, 'clean')
        self.assertEqual(self.move.anomaly_alert_count, 0)

        # Create medium risk alert
        alert1 = self.env['account.anomaly.alert'].create({
            'title': 'Test Alert 1',
            'description': 'Medium risk alert',
            'alert_type': 'amount_outlier',
            'risk_level': 'medium',
            'anomaly_score': 50,
            'move_id': self.move.id,
            'company_id': self.company.id,
        })
        self.move._compute_anomaly_alert_count()
        self.move._compute_anomaly_risk_level()
        self.assertEqual(self.move.anomaly_alert_count, 1)
        self.assertEqual(self.move.anomaly_risk_level, 'medium')

        # Create critical risk alert
        alert2 = self.env['account.anomaly.alert'].create({
            'title': 'Test Alert 2',
            'description': 'Critical risk alert',
            'alert_type': 'duplicate_vendor_bill',
            'risk_level': 'critical',
            'anomaly_score': 95,
            'move_id': self.move.id,
            'company_id': self.company.id,
        })
        self.move._compute_anomaly_alert_count()
        self.move._compute_anomaly_risk_level()
        self.assertEqual(self.move.anomaly_alert_count, 2)
        self.assertEqual(self.move.anomaly_risk_level, 'critical')

        # Resolve critical alert -> risk level drops to medium
        alert2.write({'state': 'resolved', 'resolution_note': 'Resolved'})
        self.move._compute_anomaly_alert_count()
        self.move._compute_anomaly_risk_level()
        self.assertEqual(self.move.anomaly_alert_count, 1)
        self.assertEqual(self.move.anomaly_risk_level, 'medium')

        # Mark medium alert as false positive -> risk level returns to clean
        alert1.write({'state': 'false_positive'})
        self.move._compute_anomaly_alert_count()
        self.move._compute_anomaly_risk_level()
        self.assertEqual(self.move.anomaly_alert_count, 0)
        self.assertEqual(self.move.anomaly_risk_level, 'clean')

    def test_02_action_post_scan_trigger(self):
        """Test that posting journal entry runs anomaly detection hooks when enabled."""
        self.company.anomaly_scan_on_post = True
        self.move.action_post()
        self.assertEqual(self.move.state, 'posted')

    def test_03_action_view_anomaly_alerts(self):
        """Test window action returning anomaly alerts for journal entry."""
        action = self.move.action_view_anomaly_alerts()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'account.anomaly.alert')
        self.assertEqual(action['view_mode'], 'tree,form')
        self.assertIn(('move_id', '=', self.move.id), action['domain'])
