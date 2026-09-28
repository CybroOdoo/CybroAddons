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
from odoo.exceptions import UserError
from odoo import fields
from datetime import timedelta


@tagged('post_install', '-at_install')
class TestAnomalyScanWizard(common.TransactionCase):
    """Test suite for wizard/anomaly_scan_wizard.py methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.wizard = cls.env['account.anomaly.scan.wizard'].create({
            'date_from': fields.Date.today() - timedelta(days=10),
            'date_to': fields.Date.today(),
            'company_ids': [(6, 0, [cls.company.id])],
        })

    def test_action_run_scan_invalid_dates(self):
        """Test action_run_scan method raises UserError when date_from > date_to."""
        self.wizard.date_from = fields.Date.today() + timedelta(days=5)
        self.wizard.date_to = fields.Date.today()
        with self.assertRaises(UserError):
            self.wizard.action_run_scan()

    def test_action_run_scan_success(self):
        """Test action_run_scan method runs full scan and returns action."""
        self.wizard.date_from = fields.Date.today() - timedelta(days=10)
        self.wizard.date_to = fields.Date.today()
        action = self.wizard.action_run_scan()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'account.anomaly.alert')
        self.assertIn('anomaly_scan_summary', action['context'])
