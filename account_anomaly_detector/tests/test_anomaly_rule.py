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
class TestAccountAnomalyRule(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        cls.rule = cls.env['account.anomaly.rule'].create({
            'name': 'High Amount Rule',
            'rule_type': 'amount_threshold',
            'min_amount': 5000.0,
            'score': 85,
            'company_id': cls.company.id,
        })

    def test_01_rule_risk_level_computation(self):
        """Test computed risk level based on rule score."""
        rule = self.rule
        rule.score = 25
        rule._compute_risk_level()
        self.assertEqual(rule.risk_level, 'low')

        rule.score = 50
        rule._compute_risk_level()
        self.assertEqual(rule.risk_level, 'medium')

        rule.score = 80
        rule._compute_risk_level()
        self.assertEqual(rule.risk_level, 'high')

        rule.score = 95
        rule._compute_risk_level()
        self.assertEqual(rule.risk_level, 'critical')

    def test_02_rule_hits_count_computation(self):
        """Test calculation of rule hits count."""
        rule = self.rule
        self.assertEqual(rule.hits_count, 0)

        alert = self.env['account.anomaly.alert'].create({
            'title': 'Rule Triggered Alert',
            'description': 'Triggered by custom rule',
            'alert_type': 'manual',
            'rule_id': rule.id,
            'ml_details': f'rule:{rule.id}',
            'company_id': self.company.id,
        })
        self.assertTrue(alert)

        rule._compute_hits_count()
        self.assertEqual(rule.hits_count, 1)
