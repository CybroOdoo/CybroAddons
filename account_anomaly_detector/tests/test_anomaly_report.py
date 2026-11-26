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
class TestAnomalyReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        cls.alert = cls.env['account.anomaly.alert'].create({
            'title': 'Report Test Alert',
            'description': 'Report test description',
            'alert_type': 'amount_outlier',
            'risk_level': 'high',
            'anomaly_score': 80,
            'company_id': cls.company.id,
        })

    def test_01_report_values_with_docids(self):
        """Test report data values calculation with explicit record IDs."""
        report_model = self.env['report.account_anomaly_detector.report_anomaly_alerts_document']
        res = report_model._get_report_values([self.alert.id])
        self.assertIn('docs', res)
        self.assertEqual(len(res['docs']), 1)
        self.assertEqual(res['docs'][0].id, self.alert.id)

    def test_02_report_values_without_docids(self):
        """Test report data values fallback when docids list is empty."""
        report_model = self.env['report.account_anomaly_detector.report_anomaly_alerts_document']
        res = report_model._get_report_values([])
        self.assertIn('docs', res)
        self.assertTrue(len(res['docs']) > 0)
