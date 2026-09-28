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
class TestAnomalyReport(common.TransactionCase):
    """Test suite for report/anomaly_report.py methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.report_model = cls.env['report.account_anomaly_detector.report_anomaly_alerts_document']
        cls.alert = cls.env['account.anomaly.alert'].create({
            'title': 'Report Test Alert',
            'description': 'Description for report test',
            'alert_type': 'amount_outlier',
            'anomaly_score': 85,
            'risk_level': 'high',
            'company_id': cls.company.id,
        })

    def test_get_report_values_with_docids(self):
        """Test _get_report_values method when docids are provided."""
        res = cls = self.report_model._get_report_values(docids=[self.alert.id])
        self.assertEqual(res['doc_ids'], [self.alert.id])
        self.assertEqual(res['doc_model'], 'account.anomaly.alert')
        self.assertIn(self.alert, res['docs'])

    def test_get_report_values_without_docids(self):
        """Test _get_report_values method fallback when docids is empty."""
        res = self.report_model._get_report_values(docids=[])
        self.assertEqual(res['doc_model'], 'account.anomaly.alert')
        self.assertIn(self.alert, res['docs'])
