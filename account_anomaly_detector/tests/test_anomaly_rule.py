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
class TestAnomalyRule(common.TransactionCase):
    """Test suite for models/anomaly_rule.py methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.rule = cls.env['account.anomaly.rule'].create({
            'name': 'Test Detection Rule',
            'rule_type': 'amount_threshold',
            'min_amount': 1000.0,
            'max_amount': 5000.0,
            'score': 45,
            'risk_level': 'medium',
            'company_id': cls.company.id,
        })

    def test_compute_risk_level(self):
        """Test _compute_risk_level method on anomaly rules."""
        rule = self.rule
        rule.score = 25
        rule._compute_risk_level()
        self.assertEqual(rule.risk_level, 'low')

        rule.score = 55
        rule._compute_risk_level()
        self.assertEqual(rule.risk_level, 'medium')

        rule.score = 75
        rule._compute_risk_level()
        self.assertEqual(rule.risk_level, 'high')

        rule.score = 95
        rule._compute_risk_level()
        self.assertEqual(rule.risk_level, 'critical')

    def test_compute_hits_count(self):
        """Test _compute_hits_count method."""
        self.rule._compute_hits_count()
        self.assertEqual(self.rule.hits_count, 0)

        # Create alert linked to rule
        alert = self.env['account.anomaly.alert'].create({
            'title': 'Rule Alert',
            'description': 'Description',
            'alert_type': 'manual',
            'anomaly_score': 45,
            'risk_level': 'medium',
            'company_id': self.company.id,
            'ml_details': f'rule:{self.rule.id}',
        })

        self.rule._compute_hits_count()
        self.assertEqual(self.rule.hits_count, 1)
