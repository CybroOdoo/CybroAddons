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
from datetime import timedelta
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError
from odoo import fields


@tagged('post_install', '-at_install')
class TestAnomalyScanWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

    def test_01_wizard_date_validation(self):
        """Test wizard date validation when date_from > date_to."""
        today = fields.Date.today()
        with self.assertRaises(ValidationError):
            self.env['account.anomaly.scan.wizard'].create({
                'date_from': today,
                'date_to': today - timedelta(days=5),
                'company_ids': [(4, self.company.id)],
            })

    def test_01_b_future_date_validation(self):
        """Test wizard date validation when date is in the future."""
        today = fields.Date.today()
        with self.assertRaises(ValidationError):
            self.env['account.anomaly.scan.wizard'].create({
                'date_from': today - timedelta(days=5),
                'date_to': today + timedelta(days=5),
                'company_ids': [(4, self.company.id)],
            })

    def test_01_c_onchange_date_validation(self):
        """Test onchange date validation warning."""
        today = fields.Date.today()
        wizard = self.env['account.anomaly.scan.wizard'].new({
            'date_from': today,
            'date_to': today - timedelta(days=5),
        })
        res = wizard._onchange_dates()
        self.assertIn('warning', res)
        self.assertEqual(res['warning']['title'], "Invalid Date Selection")

    def test_02_wizard_run_scan_action(self):
        """Test executing targeted anomaly scan wizard."""
        today = fields.Date.today()
        wizard = self.env['account.anomaly.scan.wizard'].create({
            'date_from': today - timedelta(days=30),
            'date_to': today,
            'company_ids': [(4, self.company.id)],
            'scan_amount_outliers': True,
            'scan_duplicates': True,
        })
        action = wizard.action_run_scan()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'account.anomaly.alert')
        self.assertEqual(action['view_mode'], 'tree,form')
        self.assertIn('anomaly_scan_summary', action['context'])
